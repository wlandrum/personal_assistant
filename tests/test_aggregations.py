import uuid
from assistant.data.db import connect, apply_schema
from assistant.data.store import UserStore


def make_user(conn, name):
    cur = conn.execute("INSERT INTO users (name) VALUES (%s) RETURNING id", (name,))
    return str(cur.fetchone()[0])


def test_spending_by_category_isolated():
    conn = connect()
    apply_schema(conn)
    a = make_user(conn, f"a_{uuid.uuid4()}")
    b = make_user(conn, f"b_{uuid.uuid4()}")
    sa = UserStore(conn, a)
    sa.add_transactions("csv", [
        {"external_id": "1", "date": "2026-06-01", "name": "Sweetgreen", "amount": 10.0},
        {"external_id": "2", "date": "2026-06-02", "name": "Sweetgreen", "amount": 5.0},
        {"external_id": "3", "date": "2026-06-03", "name": "Shell", "amount": 40.0},
    ])
    rows = sa.get_uncategorized()
    for r in rows:
        sa.set_category(r["id"], "dining" if "sweetgreen" in r["name"].lower() else "transportation")

    by_cat = {d["category"]: d["total"] for d in sa.spending_by_category()}
    assert by_cat["dining"] == 15.0
    assert by_cat["transportation"] == 40.0
    assert UserStore(conn, b).spending_by_category() == []
