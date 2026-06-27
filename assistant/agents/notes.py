import json
from datetime import date
from assistant.data.store import UserStore
from assistant.llm.factory import get_provider
from assistant.agents.actions import PendingAction
from assistant.connectors.calendar_service import create_all_day_event


def _notes_prompt() -> str:
    today = date.today().isoformat()
    return (
        f"Today is {today}. You are a note-processing assistant. "
        "Read the user's raw note and return a JSON object only, "
        "with no preamble and no code fences. Use this shape:\n"
        "{\n"
        '  "summary": "two or three sentence summary",\n'
        '  "category": "a short category label",\n'
        '  "action_items": [{"text": "...", "due_date": "YYYY-MM-DD or null"}]\n'
        "}\n"
        "If there are no action items, use an empty list. "
        "Only include a due_date when the note clearly implies one. "
        "Resolve relative dates like 'next Friday' or 'by July 3rd' against today's date.\n\n"
        "Raw note:\n"
    )


def _parse_json(raw: str) -> dict:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1:
        cleaned = cleaned[start:end + 1]
    return json.loads(cleaned)


class NotesSubagent:
    name = "note"

    def __init__(self, conn, settings, embedder):
        self.conn = conn
        self.settings = settings
        self.embedder = embedder

    def handle(self, owner_id: str, message: str):
        provider = get_provider(self.settings, "workhorse")
        raw = provider.complete(_notes_prompt() + message)
        data = _parse_json(raw)

        summary = data.get("summary", "").strip()
        category = data.get("category", "uncategorized").strip()
        action_items = data.get("action_items", []) or []

        store = UserStore(self.conn, owner_id)
        store.add_note(message, summary, category, action_items)

        vec = self.embedder.embed(summary)
        store.add_episode(summary, vec)

        saved_lines = [f"Saved a note in category '{category}'.", f"Summary: {summary}"]
        if action_items:
            saved_lines.append("Action items:")
            for item in action_items:
                due = item.get("due_date")
                suffix = f" (due {due})" if due else ""
                saved_lines.append(f"- {item['text']}{suffix}")
        saved_text = "\n".join(saved_lines)

        dated = [i for i in action_items if i.get("due_date")]
        if not dated:
            return saved_text

        offer_lines = [saved_text, "", "I can add these dated items to your calendar:"]
        for item in dated:
            offer_lines.append(f"- {item['text']} on {item['due_date']}")
        offer = "\n".join(offer_lines)

        conn = self.conn
        settings = self.settings

        def execute() -> str:
            results = []
            for item in dated:
                link = create_all_day_event(conn, settings, owner_id, item["text"], item["due_date"])
                if link is None:
                    return "Note is saved, but there is no Google Calendar connection to add events. Run connect_google first."
                results.append(f"- {item['text']}: {link}")
            return "Added to your calendar:\n" + "\n".join(results)

        return PendingAction(summary=offer, execute=execute)
