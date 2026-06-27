import json
from assistant.data.store import UserStore
from assistant.llm.factory import get_provider
from assistant.connectors.gmail_client import GoogleGmailClient
from assistant.agents.actions import PendingAction

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

    def handle(self, owner_id: str, message: str):
        token = UserStore(self.conn, owner_id).get_credential("gmail")
        if not token:
            return "No Gmail connection found. Run connect_google <owner_id> gmail first."
        client = GoogleGmailClient(token)

        if self._intent(message) == "cleanup":
            return self._propose_cleanup(owner_id, client)
        return self._triage(owner_id, client)

    def _intent(self, message: str) -> str:
        prompt = (
            "Does the user want to (a) read, triage, or summarize their inbox, "
            "or (b) clean up, organize, archive, or delete mail? "
            "Answer with one word: triage or cleanup.\n\n" + message
        )
        small = get_provider(self.settings, "router")
        answer = small.complete(prompt).strip().lower()
        return "cleanup" if "cleanup" in answer else "triage"

    def _fetch_and_classify(self, client):
        ids = client.list_recent(max_results=20)
        messages = [client.get_message(mid) for mid in ids]
        if not messages:
            return [], {}
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
        return messages, by_index

    def _triage(self, owner_id: str, client) -> str:
        messages, by_index = self._fetch_and_classify(client)
        if not messages:
            return "Your inbox has no recent messages to triage."

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

    def _propose_cleanup(self, owner_id: str, client):
        messages, by_index = self._fetch_and_classify(client)
        if not messages:
            return "Your inbox has no recent messages to clean up."

        to_archive = [messages[i] for i in range(len(messages)) if by_index.get(i) == "newsletter"]
        to_trash = [messages[i] for i in range(len(messages)) if by_index.get(i) == "promotional"]

        if not to_archive and not to_trash:
            return (
                "Nothing matched the cleanup policy. Newsletters get archived and promotional "
                "mail goes to Trash, and none were found."
            )

        lines = ["Proposed inbox cleanup:"]
        if to_archive:
            lines.append(f"Archive {len(to_archive)} newsletters:")
            lines += [f"- {m['subject']} (from {m['from']})" for m in to_archive]
        if to_trash:
            lines.append(f"Move {len(to_trash)} promotional emails to Trash (recoverable for 30 days):")
            lines += [f"- {m['subject']} (from {m['from']})" for m in to_trash]
        summary = "\n".join(lines)

        conn = self.conn

        def execute() -> str:
            for m in to_archive:
                client.archive(m["id"])
                UserStore(conn, owner_id).add_audit("gmail_archive", m["subject"])
            for m in to_trash:
                client.trash(m["id"])
                UserStore(conn, owner_id).add_audit("gmail_trash", m["subject"])
            return (
                f"Done. Archived {len(to_archive)} newsletters and moved {len(to_trash)} "
                "promotional emails to Trash. Trash is recoverable for 30 days."
            )

        return PendingAction(summary=summary, execute=execute)
