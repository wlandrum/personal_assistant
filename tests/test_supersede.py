import uuid
from assistant.data.db import connect, apply_schema
from assistant.data.store import UserStore


def make_user(conn, name):
    cur = conn.execute("INSERT INTO users (name) VALUES (%s) RETURNING id", (name,))
    return str(cur.fetchone()[0])


def test_supersede_replaces_active_value():
    conn = connect()
    apply_schema(conn)
    u = make_user(conn, f"u_{uuid.uuid4()}")
    store = UserStore(conn, u)

    store.add_fact("bank", "Chase")
    store.supersede_fact("bank", "Ally")

    facts = store.get_active_facts()
    banks = [f["value"] for f in facts if f["key"] == "bank"]
    assert banks == ["Ally"]
