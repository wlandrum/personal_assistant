import json
from assistant.agents.calendar import CalendarSubagent
from assistant.agents.actions import PendingAction


class FakeWorkhorse:
    def complete(self, prompt, system=None):
        return json.dumps({
            "title": "Lunch with Miles",
            "start": "2026-07-01T12:00:00",
            "end": "2026-07-01T13:00:00",
            "description": "",
        })


def test_calendar_proposes_not_writes(monkeypatch):
    settings = type("S", (), {"timezone": "America/New_York"})()
    agent = CalendarSubagent(conn=None, settings=settings)
    monkeypatch.setattr("assistant.agents.calendar.get_provider", lambda s, tier: FakeWorkhorse())

    result = agent.handle("u1", "lunch with Miles next Tuesday at noon")
    assert isinstance(result, PendingAction)
    assert "Lunch with Miles" in result.summary
