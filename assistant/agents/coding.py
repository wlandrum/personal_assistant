import os
from assistant.data.store import UserStore
from assistant.llm.factory import get_provider

CODING_SYSTEM = (
    "You are a senior software engineer. Write correct, idiomatic, well-structured code "
    "with a brief, clear explanation. Call out edge cases and tradeoffs when they matter. "
    "Do not pad the answer."
)

DIFFICULTY_PROMPT = (
    "Classify this coding request as 'simple' or 'hard'. "
    "Hard means it needs deep reasoning, non-trivial algorithms, architecture or design decisions, "
    "or debugging a subtle problem. Simple means a small snippet, a syntax question, or a short function. "
    "Answer with one word: simple or hard.\n\n"
)

OVERRIDE_PHRASES = ("use the big model", "use claude", "[hard]", "think hard")


class CodingSubagent:
    name = "code"

    def __init__(self, conn, settings, embedder=None):
        self.conn = conn
        self.settings = settings

    def _select_tier(self, message: str) -> str:
        lowered = message.lower()
        if any(p in lowered for p in OVERRIDE_PHRASES):
            return "frontier"
        small = get_provider(self.settings, "router")
        verdict = small.complete(DIFFICULTY_PROMPT + message).strip().lower()
        return "frontier" if "hard" in verdict else "workhorse"

    def handle(self, owner_id: str, message: str) -> str:
        tier = self._select_tier(message)

        note = ""
        if tier == "frontier" and not os.environ.get("ANTHROPIC_API_KEY"):
            tier = "workhorse"
            note = "(Claude was selected but no API key is set, so the local model answered instead.)\n\n"

        provider = get_provider(self.settings, tier)
        answer = provider.complete(message, system=CODING_SYSTEM)

        UserStore(self.conn, owner_id).add_audit("coding_query", f"tier={tier}")
        return note + answer
