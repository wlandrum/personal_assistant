import json
from assistant.data.store import UserStore
from assistant.llm.factory import get_provider

NOTES_PROMPT = (
    "You are a note-processing assistant. Read the user's raw note and return a JSON object only, "
    "with no preamble and no code fences. Use this shape:\n"
    "{\n"
    '  "summary": "two or three sentence summary",\n'
    '  "category": "a short category label",\n'
    '  "action_items": [{"text": "...", "due_date": "YYYY-MM-DD or null"}]\n'
    "}\n"
    "If there are no action items, use an empty list. Only include a due_date when the note clearly implies one.\n\n"
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

    def handle(self, owner_id: str, message: str) -> str:
        provider = get_provider(self.settings, "workhorse")
        raw = provider.complete(NOTES_PROMPT + message)
        data = _parse_json(raw)

        summary = data.get("summary", "").strip()
        category = data.get("category", "uncategorized").strip()
        action_items = data.get("action_items", []) or []

        store = UserStore(self.conn, owner_id)
        store.add_note(message, summary, category, action_items)

        vec = self.embedder.embed(summary)
        store.add_episode(summary, vec)

        lines = [f"Saved a note in category '{category}'.", f"Summary: {summary}"]
        if action_items:
            lines.append("Action items:")
            for item in action_items:
                due = item.get("due_date")
                suffix = f" (due {due})" if due else ""
                lines.append(f"- {item['text']}{suffix}")
        return "\n".join(lines)
