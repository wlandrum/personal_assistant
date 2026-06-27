import uuid
from assistant.data.db import connect, apply_schema
from assistant.data.store import UserStore
from assistant.agents.critic import CriticSubagent
from assistant.config import load_settings


class FakeEmbedder:
    def embed(self, text):
        return [0.1] * 768


class FakeProvider:
    def complete(self, prompt, system=None):
        return "reasoning text"


def make_user(conn, name):
    cur = conn.execute("INSERT INTO users (name) VALUES (%s) RETURNING id", (name,))
    return str(cur.fetchone()[0])


def test_resolve_records_decision_and_memory(monkeypatch):
    conn = connect()
    apply_schema(conn)
    u = make_user(conn, f"u_{uuid.uuid4()}")
    critic = CriticSubagent(conn, load_settings(), FakeEmbedder())
    monkeypatch.setattr("assistant.agents.critic.provider_for", lambda s, w: (FakeProvider(), "workhorse", ""))

    out = critic.resolve(u, "launch the consulting practice", [], "accept")
    assert "accept" in out.lower()

    decisions = UserStore(conn, u).get_decisions()
    assert len(decisions) == 1
    assert decisions[0]["verdict"] == "accept"

    episodes = UserStore(conn, u).search_episodes([0.1] * 768, k=10)
    assert any("consulting practice" in e["summary"] for e in episodes)


def test_terminal_detection(monkeypatch):
    critic = CriticSubagent(None, load_settings(), FakeEmbedder())

    class Small:
        def __init__(self, word):
            self.word = word

        def complete(self, prompt, system=None):
            return self.word

    import assistant.llm.factory as f
    monkeypatch.setattr(f, "get_provider", lambda s, tier: Small("accept"))
    assert critic.detect_terminal("yes let us do it") == "accept"
    monkeypatch.setattr(f, "get_provider", lambda s, tier: Small("continue"))
    assert critic.detect_terminal("but what about cost") == "continue"


def test_orchestrator_flow(monkeypatch):
    import assistant.orchestrator.orchestrator as o
    conn = connect()
    apply_schema(conn)
    u = make_user(conn, f"u_{uuid.uuid4()}")

    monkeypatch.setattr(o, "classify", lambda provider, message: "critic")
    monkeypatch.setattr(o, "get_provider", lambda settings, tier: object())

    orch = o.Orchestrator.__new__(o.Orchestrator)
    orch.settings = load_settings()
    orch.conn = conn
    orch.subagents = {}
    orch.pending = {}
    orch.critiques = {}

    class FakeCritic:
        def open(self, owner_id, idea):
            return "opening critique"

        def detect_terminal(self, message):
            return "accept" if "accept" in message else "continue"

        def round(self, owner_id, message, history):
            return "another round"

        def resolve(self, owner_id, idea, history, verdict):
            return f"resolved as {verdict}"

    orch.critic = FakeCritic()

    first = orch.respond(u, "I want to switch banks")
    assert "opening critique" in first
    assert u in orch.critiques

    second = orch.respond(u, "but is the timing right")
    assert "another round" in second
    assert u in orch.critiques

    third = orch.respond(u, "ok I accept")
    assert "resolved as accept" in third
    assert u not in orch.critiques
