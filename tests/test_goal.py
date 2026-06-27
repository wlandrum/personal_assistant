import uuid
from assistant.data.db import connect, apply_schema
from assistant.data.store import UserStore
from assistant.agents.finance import FinanceSubagent
from assistant.config import load_settings


def make_user(conn, name):
    cur = conn.execute("INSERT INTO users (name) VALUES (%s) RETURNING id", (name,))
    return str(cur.fetchone()[0])


class FakePlanner:
    def complete(self, prompt, system=None):
        return "1. Trim dining by 20 percent. 2. Redirect the savings."


def test_goal_uses_real_numbers_and_audits(monkeypatch):
    conn = connect()
    apply_schema(conn)
    u = make_user(conn, f"u_{uuid.uuid4()}")
    store = UserStore(conn, u)
    store.add_transactions("csv", [{"external_id": "1", "date": "2026-06-01", "name": "Sweetgreen", "amount": 50.0}])
    for r in store.get_uncategorized():
        store.set_category(r["id"], "dining")

    settings = load_settings()
    agent = FinanceSubagent(conn, settings)
    monkeypatch.setattr("assistant.agents.finance.provider_for", lambda s, w: (FakePlanner(), "workhorse", ""))

    out = agent._goal(u, "I want to save 2000 dollars in 6 months")
    assert "Trim dining" in out
    assert "not professional financial advice" in out
    assert any(a["action"] == "finance_goal" for a in store.get_audit())
