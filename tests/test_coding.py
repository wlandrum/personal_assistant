import uuid
from assistant.data.db import connect, apply_schema
from assistant.data.store import UserStore
from assistant.agents.coding import CodingSubagent
from assistant.config import load_settings


class TierRecorder:
    def __init__(self, verdict):
        self.verdict = verdict
        self.tiers = []

    def for_tier(self, tier):
        self.tiers.append(tier)
        recorder = self

        class P:
            def complete(self, prompt, system=None):
                if tier == "router":
                    return recorder.verdict
                return f"answer from {tier}"

        return P()


def make_user(conn, name):
    cur = conn.execute("INSERT INTO users (name) VALUES (%s) RETURNING id", (name,))
    return str(cur.fetchone()[0])


def test_simple_uses_workhorse(monkeypatch):
    conn = connect()
    apply_schema(conn)
    u = make_user(conn, f"u_{uuid.uuid4()}")
    rec = TierRecorder("simple")
    agent = CodingSubagent(conn, load_settings())
    monkeypatch.setattr("assistant.agents.coding.get_provider", lambda s, tier: rec.for_tier(tier))

    out = agent.handle(u, "write a function to add two numbers")
    assert "workhorse" in out
    assert "workhorse" in rec.tiers
    assert "frontier" not in rec.tiers
    assert any(a["detail"] == "tier=workhorse" for a in UserStore(conn, u).get_audit())


def test_hard_uses_frontier(monkeypatch):
    conn = connect()
    apply_schema(conn)
    u = make_user(conn, f"u_{uuid.uuid4()}")
    rec = TierRecorder("hard")
    agent = CodingSubagent(conn, load_settings())
    monkeypatch.setattr("assistant.agents.coding.get_provider", lambda s, tier: rec.for_tier(tier))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    out = agent.handle(u, "design a sliding window rate limiter and explain the tradeoffs")
    assert "frontier" in out
    assert "frontier" in rec.tiers


def test_frontier_falls_back_without_key(monkeypatch):
    conn = connect()
    apply_schema(conn)
    u = make_user(conn, f"u_{uuid.uuid4()}")
    rec = TierRecorder("hard")
    agent = CodingSubagent(conn, load_settings())
    monkeypatch.setattr("assistant.agents.coding.get_provider", lambda s, tier: rec.for_tier(tier))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    out = agent.handle(u, "design a complex distributed lock")
    assert "no API key" in out
    assert "workhorse" in out
    assert any(a["detail"] == "tier=workhorse" for a in UserStore(conn, u).get_audit())
