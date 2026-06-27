import uuid
import pytest
from assistant.data.db import connect, apply_schema
from assistant.data.store import UserStore
from assistant.orchestrator.orchestrator import Orchestrator


class FakeProvider:
    def __init__(self):
        self.last_system = None
        self.last_prompt = None

    def complete(self, prompt, system=None):
        self.last_system = system
        self.last_prompt = prompt
        return "ok"


class FakeEmbedder:
    def embed(self, text):
        return [0.1] * 768


@pytest.fixture
def conn():
    c = connect()
    apply_schema(c)
    return c


def make_user(conn, name):
    cur = conn.execute("INSERT INTO users (name) VALUES (%s) RETURNING id", (name,))
    return str(cur.fetchone()[0])


def test_context_contains_only_owner_data(conn, monkeypatch):
    a = make_user(conn, f"a_{uuid.uuid4()}")
    b = make_user(conn, f"b_{uuid.uuid4()}")

    UserStore(conn, a).add_fact("secret", "alpha-secret")
    UserStore(conn, b).add_fact("secret", "bravo-secret")
    UserStore(conn, a).add_episode("alpha private episode", [0.1] * 768)
    UserStore(conn, b).add_episode("bravo private episode", [0.1] * 768)

    provider = FakeProvider()
    monkeypatch.setattr("assistant.orchestrator.orchestrator.get_provider", lambda s, tier: provider)
    monkeypatch.setattr("assistant.orchestrator.orchestrator.classify", lambda p, m: "chat")

    orch = Orchestrator(conn, None, FakeEmbedder())
    orch.respond(a, "what is my secret")

    assert "alpha-secret" in provider.last_system
    assert "bravo-secret" not in provider.last_system
    assert "alpha private episode" in provider.last_system
    assert "bravo private episode" not in provider.last_system


def test_remember_stores_under_correct_owner(conn, monkeypatch):
    a = make_user(conn, f"a_{uuid.uuid4()}")
    b = make_user(conn, f"b_{uuid.uuid4()}")

    provider = FakeProvider()
    provider.complete = lambda prompt, system=None: "a distilled summary"
    monkeypatch.setattr("assistant.orchestrator.orchestrator.get_provider", lambda s, tier: provider)

    orch = Orchestrator(conn, None, FakeEmbedder())
    orch.remember(a, [{"role": "user", "content": "hello"}])

    a_episodes = UserStore(conn, a).search_episodes([0.1] * 768, k=10)
    b_episodes = UserStore(conn, b).search_episodes([0.1] * 768, k=10)
    assert any("distilled summary" in e["summary"] for e in a_episodes)
    assert all("distilled summary" not in e["summary"] for e in b_episodes)
