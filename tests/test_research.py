import uuid
from assistant.data.db import connect, apply_schema
from assistant.data.store import UserStore
from assistant.agents.research_agent import ResearchSubagent
from assistant.config import load_settings


class FakeProvider:
    def research(self, query):
        return {"answer": "Synthesized answer.", "citations": ["http://src.com"]}


def make_user(conn, name):
    cur = conn.execute("INSERT INTO users (name) VALUES (%s) RETURNING id", (name,))
    return str(cur.fetchone()[0])


def test_research_formats_and_audits(monkeypatch):
    conn = connect()
    apply_schema(conn)
    u = make_user(conn, f"u_{uuid.uuid4()}")
    settings = load_settings()

    agent = ResearchSubagent(conn, settings)
    monkeypatch.setattr("assistant.agents.research_agent.get_research_provider", lambda s: FakeProvider())

    result = agent.handle(u, "what is the latest on the mars mission")
    assert "Synthesized answer." in result
    assert "http://src.com" in result

    audits = UserStore(conn, u).get_audit()
    assert any(a["action"] == "research" for a in audits)

    other = make_user(conn, f"o_{uuid.uuid4()}")
    assert UserStore(conn, other).get_audit() == []
