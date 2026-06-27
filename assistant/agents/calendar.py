import json
from datetime import date
from assistant.llm.factory import get_provider
from assistant.connectors.calendar_service import create_timed_event
from assistant.agents.actions import PendingAction


def _parse_json(raw: str) -> dict:
    cleaned = raw.strip().strip("`")
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1:
        cleaned = cleaned[start:end + 1]
    return json.loads(cleaned)


class CalendarSubagent:
    name = "calendar"

    def __init__(self, conn, settings, embedder=None):
        self.conn = conn
        self.settings = settings

    def handle(self, owner_id: str, message: str):
        tz = self.settings.timezone
        today = date.today().isoformat()
        prompt = (
            f"Today is {today} in timezone {tz}. Extract a calendar event from the user's request. "
            "Return JSON only, no code fences, with this shape:\n"
            '{"title": "...", "start": "YYYY-MM-DDTHH:MM:SS", "end": "YYYY-MM-DDTHH:MM:SS", "description": "..."}\n'
            "Resolve relative dates like next Tuesday against today. Default events to one hour if no end is given.\n\n"
            "Request:\n" + message
        )
        provider = get_provider(self.settings, "workhorse")
        data = _parse_json(provider.complete(prompt))

        title = data["title"]
        start_iso = data["start"]
        end_iso = data["end"]
        description = data.get("description", "")

        summary = f"Create calendar event '{title}' from {start_iso} to {end_iso} ({tz})."

        conn = self.conn
        settings = self.settings

        def execute() -> str:
            link = create_timed_event(conn, settings, owner_id, title, start_iso, end_iso, description)
            if link is None:
                return "No Google Calendar connection found. Run connect_google first."
            return f"Event created: {link}"

        return PendingAction(summary=summary, execute=execute)
