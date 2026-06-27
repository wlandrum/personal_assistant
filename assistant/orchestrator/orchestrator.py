from assistant.data.store import UserStore
from assistant.orchestrator.context import build_context


def _format_history(history):
    if not history:
        return ""
    parts = []
    for turn in history:
        parts.append(f"{turn['role']}: {turn['content']}")
    return "\n".join(parts)


class Orchestrator:
    def __init__(self, conn, provider, embedder):
        self.conn = conn
        self.provider = provider
        self.embedder = embedder

    def respond(self, owner_id: str, message: str, history=None) -> str:
        store = UserStore(self.conn, owner_id)
        system = build_context(store, self.embedder, message)
        prior = _format_history(history)
        prompt = message if not prior else f"{prior}\nuser: {message}"
        return self.provider.complete(prompt, system=system)

    def remember(self, owner_id: str, turns) -> str:
        store = UserStore(self.conn, owner_id)
        transcript = _format_history(turns)
        summary_prompt = (
            "Summarize this conversation in two or three sentences. "
            "Capture any decisions made and any durable facts about the user. "
            "Be concise and factual.\n\n" + transcript
        )
        summary = self.provider.complete(summary_prompt)
        vec = self.embedder.embed(summary)
        store.add_episode(summary, vec)
        return summary
