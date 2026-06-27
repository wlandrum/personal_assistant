import json
import uuid
from assistant.data.db import connect, apply_schema
from assistant.data.store import UserStore
from assistant.agents.email import EmailSubagent
from assistant.config import load_settings


class FakeGmail:
    def list_recent(self, max_results=20):
        return ["1", "2"]

    def get_message(self, mid):
        data = {
            "1": {"id": "1", "from": "boss@work.com", "subject": "Need the report", "date": "", "snippet": "by friday"},
            "2": {"id": "2", "from": "deals@store.com", "subject": "50% off", "date": "", "snippet": "sale"},
        }
        return data[mid]


class FakeSmall:
    def complete(self, prompt, system=None):
        return json.dumps([{"index": 0, "category": "important"}, {"index": 1, "category": "promotional"}])


class FakeWorkhorse:
    def complete(self, prompt, system=None):
        return "Boss needs the report by Friday."


def make_user(conn, name):
    cur = conn.execute("INSERT INTO users (name) VALUES (%s) RETURNING id", (name,))
    return str(cur.fetchone()[0])


def test_triage_builds_digest_and_audits(monkeypatch):
    conn = connect()
    apply_schema(conn)
    u = make_user(conn, f"u_{uuid.uuid4()}")
    settings = load_settings()

    agent = EmailSubagent(conn, settings)
    monkeypatch.setattr("assistant.agents.email.UserStore.get_credential", lambda self, provider: "token")
    monkeypatch.setattr("assistant.agents.email.GoogleGmailClient", lambda token: FakeGmail())

    providers = {"router": FakeSmall(), "workhorse": FakeWorkhorse()}
    monkeypatch.setattr("assistant.agents.email.get_provider", lambda s, tier: providers[tier])

    result = agent.handle(u, "triage my inbox")
    assert "Important: 1" in result
    assert "report by Friday" in result

    audits = UserStore(conn, u).get_audit()
    assert any(a["action"] == "gmail_triage" for a in audits)


def test_audit_owner_isolation(monkeypatch):
    conn = connect()
    apply_schema(conn)
    u1 = make_user(conn, f"u1_{uuid.uuid4()}")
    u2 = make_user(conn, f"u2_{uuid.uuid4()}")
    settings = load_settings()

    agent = EmailSubagent(conn, settings)
    monkeypatch.setattr("assistant.agents.email.UserStore.get_credential", lambda self, provider: "token")
    monkeypatch.setattr("assistant.agents.email.GoogleGmailClient", lambda token: FakeGmail())

    providers = {"router": FakeSmall(), "workhorse": FakeWorkhorse()}
    monkeypatch.setattr("assistant.agents.email.get_provider", lambda s, tier: providers[tier])

    agent.handle(u1, "triage my inbox")

    assert len(UserStore(conn, u1).get_audit()) == 1
    assert len(UserStore(conn, u2).get_audit()) == 0
