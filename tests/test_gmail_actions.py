import uuid
from assistant.data.db import connect, apply_schema
from assistant.data.store import UserStore
from assistant.agents.email import EmailSubagent
from assistant.agents.actions import PendingAction
from assistant.config import load_settings


class FakeGmail:
    def __init__(self):
        self.archived = []
        self.trashed = []

    def list_recent(self, max_results=20):
        return ["1", "2", "3"]

    def get_message(self, mid):
        data = {
            "1": {"id": "1", "from": "news@site.com", "subject": "Weekly digest", "date": "", "snippet": "news"},
            "2": {"id": "2", "from": "deals@store.com", "subject": "Sale", "date": "", "snippet": "buy"},
            "3": {"id": "3", "from": "boss@work.com", "subject": "Report", "date": "", "snippet": "urgent"},
        }
        return data[mid]

    def archive(self, mid):
        self.archived.append(mid)

    def trash(self, mid):
        self.trashed.append(mid)


class FakeSmallCleanup:
    def __init__(self):
        self.calls = 0

    def complete(self, prompt, system=None):
        self.calls += 1
        if "triage or cleanup" in prompt:
            return "cleanup"
        return '[{"index":0,"category":"newsletter"},{"index":1,"category":"promotional"},{"index":2,"category":"important"}]'


def make_user(conn, name):
    cur = conn.execute("INSERT INTO users (name) VALUES (%s) RETURNING id", (name,))
    return str(cur.fetchone()[0])


def test_cleanup_proposes_then_executes(monkeypatch):
    conn = connect()
    apply_schema(conn)
    u = make_user(conn, f"u_{uuid.uuid4()}")
    settings = load_settings()

    fake_gmail = FakeGmail()
    agent = EmailSubagent(conn, settings)
    monkeypatch.setattr("assistant.agents.email.UserStore.get_credential", lambda self, provider: "token")
    monkeypatch.setattr("assistant.agents.email.GoogleGmailClient", lambda token: fake_gmail)
    monkeypatch.setattr("assistant.agents.email.get_provider", lambda s, tier: FakeSmallCleanup())

    result = agent.handle(u, "clean up my inbox")
    assert isinstance(result, PendingAction)
    assert "Weekly digest" in result.summary
    assert "Sale" in result.summary
    assert fake_gmail.archived == []
    assert fake_gmail.trashed == []

    output = result.execute()
    assert fake_gmail.archived == ["1"]
    assert fake_gmail.trashed == ["2"]
    assert "recoverable" in output.lower()

    audits = {a["action"] for a in UserStore(conn, u).get_audit()}
    assert "gmail_archive" in audits
    assert "gmail_trash" in audits


def test_important_mail_never_touched(monkeypatch):
    conn = connect()
    apply_schema(conn)
    u = make_user(conn, f"u_{uuid.uuid4()}")
    settings = load_settings()

    fake_gmail = FakeGmail()
    agent = EmailSubagent(conn, settings)
    monkeypatch.setattr("assistant.agents.email.UserStore.get_credential", lambda self, provider: "token")
    monkeypatch.setattr("assistant.agents.email.GoogleGmailClient", lambda token: fake_gmail)
    monkeypatch.setattr("assistant.agents.email.get_provider", lambda s, tier: FakeSmallCleanup())

    result = agent.handle(u, "clean up my inbox")
    result.execute()

    # message id "3" is important, must never be archived or trashed
    assert "3" not in fake_gmail.archived
    assert "3" not in fake_gmail.trashed
