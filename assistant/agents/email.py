import json
from assistant.data.store import UserStore
from assistant.llm.factory import get_provider
from assistant.connectors.gmail_client import GoogleGmailClient

CATEGORIES = ("important", "newsletter", "promotional", "other")


def _parse_json_array(raw: str):
    cleaned = raw.strip().strip("`")
    start = cleaned.find("[")
    end = cleaned.rfind("]")
    if start != -1 and end != -1:
        cleaned = cleaned[start:end + 1]
    return json.loads(cleaned)


class EmailSubagent:
    name = "email"

    def __init__(self, conn, settings, embedder=None):
        self.conn = conn
        self.settings = settings

    def handle(self, owner_id: str, message: str) -> str:
        token = UserStore(self.conn, owner_id).get_credential("gmail")
        if not token:
            return "No Gmail connection found. Run connect_google <owner_id> gmail first."

        client = GoogleGmailClient(token)
        ids = client.list_recent(max_results=20)
        messages = [client.get_message(mid) for mid in ids]

        if not messages:
            return "Your inbox has no recent messages to triage."

        listing = "\n".join(
            f"{i}. From: {m['from']} | Subject: {m['subject']} | {m['snippet'][:120]}"
            for i, m in enumerate(messages)
        )
        classify_prompt = (
            "Classify each email into one of: important, newsletter, promotional, other. "
            "Return a JSON array only, one object per email, shape: "
            '[{"index": 0, "category": "important"}].\n\n' + listing
        )
        small = get_provider(self.settings, "router")
        try:
            labels = _parse_json_array(small.complete(classify_prompt))
        except Exception:
            labels = [{"index": i, "category": "other"} for i in range(len(messages))]

        by_index = {item["index"]: item["category"] for item in labels if "index" in item}
        important = [messages[i] for i in range(len(messages)) if by_index.get(i) == "important"]

        summary = "No important messages flagged."
        if important:
            imp_listing = "\n".join(
                f"- From {m['from']}: {m['subject']}. {m['snippet'][:160]}"
                for m in important
            )
            workhorse = get_provider(self.settings, "workhorse")
            summary = workhorse.complete(
                "Summarize these important emails into a short digest of two to four sentences, "
                "noting anything that needs a reply or action.\n\n" + imp_listing
            )

        counts = {c: 0 for c in CATEGORIES}
        for c in by_index.values():
            if c in counts:
                counts[c] += 1

        UserStore(self.conn, owner_id).add_audit(
            "gmail_triage", f"triaged {len(messages)} messages"
        )

        lines = [
            f"Triaged {len(messages)} recent messages.",
            f"Important: {counts['important']}, Newsletters: {counts['newsletter']}, "
            f"Promotional: {counts['promotional']}, Other: {counts['other']}.",
            "",
            "Important digest:",
            summary,
        ]
        return "\n".join(lines)
