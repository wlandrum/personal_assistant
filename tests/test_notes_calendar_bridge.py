import json
import uuid
from assistant.data.db import connect, apply_schema
from assistant.data.store import UserStore
from assistant.agents.notes import NotesSubagent
from assistant.agents.actions import PendingAction
from assistant.config import load_settings


class FakeEmbedder:
    def embed(self, text):
        return [0.1] * 768


class DatedWorkhorse:
    def complete(self, prompt, system=None):
        return json.dumps({
            "summary": "Send the contract and prep the review.",
            "category": "work",
            "action_items": [
                {"text": "send the contract", "due_date": "2026-07-03"},
                {"text": "prep the review", "due_date": None},
            ],
        })


class UndatedWorkhorse:
    def complete(self, prompt, system=None):
        return json.dumps({
            "summary": "General thoughts about the project.",
            "category": "work",
            "action_items": [{"text": "think more", "due_date": None}],
        })


def make_user(conn, name):
    cur = conn.execute("INSERT INTO users (name) VALUES (%s) RETURNING id", (name,))
    return str(cur.fetchone()[0])


def test_dated_note_offers_calendar(monkeypatch):
    conn = connect()
    apply_schema(conn)
    u = make_user(conn, f"u_{uuid.uuid4()}")
    settings = load_settings()
    agent = NotesSubagent(conn, settings, FakeEmbedder())
    monkeypatch.setattr("assistant.agents.notes.get_provider", lambda s, tier: DatedWorkhorse())

    result = agent.handle(u, "raw note")
    assert isinstance(result, PendingAction)
    assert "send the contract on 2026-07-03" in result.summary
    assert len(UserStore(conn, u).get_notes()) == 1


def test_undated_note_returns_text(monkeypatch):
    conn = connect()
    apply_schema(conn)
    u = make_user(conn, f"u_{uuid.uuid4()}")
    settings = load_settings()
    agent = NotesSubagent(conn, settings, FakeEmbedder())
    monkeypatch.setattr("assistant.agents.notes.get_provider", lambda s, tier: UndatedWorkhorse())

    result = agent.handle(u, "raw note")
    assert isinstance(result, str)
    assert "Saved a note" in result


def test_execute_creates_events(monkeypatch):
    conn = connect()
    apply_schema(conn)
    u = make_user(conn, f"u_{uuid.uuid4()}")
    settings = load_settings()
    agent = NotesSubagent(conn, settings, FakeEmbedder())
    monkeypatch.setattr("assistant.agents.notes.get_provider", lambda s, tier: DatedWorkhorse())

    calls = []

    def fake_create(conn_, settings_, owner_id, title, day_iso, description=""):
        calls.append((owner_id, title, day_iso))
        return "http://calendar/event"

    monkeypatch.setattr("assistant.agents.notes.create_all_day_event", fake_create)

    result = agent.handle(u, "raw note")
    output = result.execute()
    assert len(calls) == 1
    assert calls[0][1] == "send the contract"
    assert "Added to your calendar" in output
