import uuid
from assistant.data.db import connect, apply_schema
from assistant.data.store import UserStore
from assistant.finance.categorize import categorize
from assistant.config import load_settings


class CountingSmall:
    def __init__(self):
        self.calls = 0

    def complete(self, prompt, system=None):
        self.calls += 1
        return '[{"index":0,"category":"dining"}]'


def make_user(conn, name):
    cur = conn.execute("INSERT INTO users (name) VALUES (%s) RETURNING id", (name,))
    return str(cur.fetchone()[0])


def test_rules_avoid_model_calls(monkeypatch):
    conn = connect()
    apply_schema(conn)
    u = make_user(conn, f"u_{uuid.uuid4()}")
    store = UserStore(conn, u)
    store.add_transactions("csv", [
        {"external_id": "a", "date": "2026-06-01", "name": "Sweetgreen", "amount": 12.5},
    ])

    small = CountingSmall()
    settings = load_settings()
    monkeypatch.setattr("assistant.finance.categorize.get_provider", lambda s, tier: small)

    rows = store.get_uncategorized()
    pairs = categorize(store, settings, rows)
    for tid, cat in pairs:
        store.set_category(tid, cat)
    assert pairs[0][1] == "dining"
    assert small.calls == 1
    assert store.get_merchant_rule("sweetgreen") == "dining"

    store.add_transactions("csv", [
        {"external_id": "b", "date": "2026-06-08", "name": "Sweetgreen", "amount": 9.0},
    ])
    rows2 = store.get_uncategorized()
    categorize(store, settings, rows2)
    assert small.calls == 1


def test_transactions_isolated(monkeypatch):
    conn = connect()
    apply_schema(conn)
    a = make_user(conn, f"a_{uuid.uuid4()}")
    b = make_user(conn, f"b_{uuid.uuid4()}")
    UserStore(conn, a).add_transactions("csv", [{"external_id": "x", "date": "2026-06-01", "name": "A store", "amount": 5.0}])
    assert len(UserStore(conn, a).get_uncategorized()) == 1
    assert len(UserStore(conn, b).get_uncategorized()) == 0
