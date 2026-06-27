import json
import uuid
from assistant.data.db import connect, apply_schema
from assistant.data.store import UserStore
from assistant.agents.notes import NotesSubagent
from assistant.config import load_settings


class FakeWorkhorse:
    def complete(self, prompt, system=None):
        return json.dumps({
            "summary": "User needs to prep for the Monday review and call the vendor.",
            "category": "work",
            "action_items": [
                {"text": "prep Monday review", "due_date": None},
                {"text": "call vendor", "due_date": "2026-07-01"},
            ],
        })


class FakeEmbedder:
    def embed(self, text):
        return [0.1] * 768


def make_user(conn, name):
    cur = conn.execute("INSERT INTO users (name) VALUES (%s) RETURNING id", (name,))
    return str(cur.fetchone()[0])


def test_notes_persist_under_owner(monkeypatch):
    conn = connect()
    apply_schema(conn)
    a = make_user(conn, f"a_{uuid.uuid4()}")
    b = make_user(conn, f"b_{uuid.uuid4()}")

    settings = load_settings()
    agent = NotesSubagent(conn, settings, FakeEmbedder())
    monkeypatch.setattr("assistant.agents.notes.get_provider", lambda s, tier: FakeWorkhorse())

    agent.handle(a, "raw note text for user a")

    a_notes = UserStore(conn, a).get_notes()
    b_notes = UserStore(conn, b).get_notes()
    assert len(a_notes) == 1
    assert len(b_notes) == 0

    a_items = UserStore(conn, a).get_action_items()
    assert {i["text"] for i in a_items} == {"prep Monday review", "call vendor"}
    assert UserStore(conn, b).get_action_items() == []
