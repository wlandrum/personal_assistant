import os
import uuid
import pytest
from assistant.data.db import connect, apply_schema
from assistant.data.store import UserStore


@pytest.fixture
def conn():
    c = connect()
    apply_schema(c)
    return c


def make_user(conn, name):
    cur = conn.execute("INSERT INTO users (name) VALUES (%s) RETURNING id", (name,))
    return str(cur.fetchone()[0])


def test_facts_are_isolated(conn):
    a = make_user(conn, f"a_{uuid.uuid4()}")
    b = make_user(conn, f"b_{uuid.uuid4()}")

    UserStore(conn, a).add_fact("bank", "Chase")
    UserStore(conn, b).add_fact("bank", "Ally")

    a_facts = UserStore(conn, a).get_active_facts()
    b_facts = UserStore(conn, b).get_active_facts()

    assert {f["value"] for f in a_facts} == {"Chase"}
    assert {f["value"] for f in b_facts} == {"Ally"}


def test_episodes_are_isolated(conn):
    a = make_user(conn, f"a_{uuid.uuid4()}")
    b = make_user(conn, f"b_{uuid.uuid4()}")

    vec = [0.1] * 768
    UserStore(conn, a).add_episode("a private note", vec)
    UserStore(conn, b).add_episode("b private note", vec)

    results = UserStore(conn, a).search_episodes(vec, k=10)
    summaries = {r["summary"] for r in results}
    assert "a private note" in summaries
    assert "b private note" not in summaries


def test_store_requires_owner(conn):
    with pytest.raises(ValueError):
        UserStore(conn, "")
