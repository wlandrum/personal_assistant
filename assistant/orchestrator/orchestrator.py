from assistant.data.store import UserStore
from assistant.orchestrator.context import build_context
from assistant.llm.factory import get_provider
from assistant.agents.router import classify
from assistant.agents.notes import NotesSubagent


def _format_history(history):
    if not history:
        return ""
    return "\n".join(f"{t['role']}: {t['content']}" for t in history)


class Orchestrator:
    def __init__(self, conn, settings, embedder):
        self.conn = conn
        self.settings = settings
        self.embedder = embedder
        self.subagents = {
            "note": NotesSubagent(conn, settings, embedder),
        }

    def respond(self, owner_id: str, message: str, history=None) -> str:
        router_provider = get_provider(self.settings, "router")
        route = classify(router_provider, message)

        if route in self.subagents:
            return self.subagents[route].handle(owner_id, message)

        return self._chat(owner_id, message, history)

    def _chat(self, owner_id: str, message: str, history=None) -> str:
        store = UserStore(self.conn, owner_id)
        system = build_context(store, self.embedder, message)
        prior = _format_history(history)
        prompt = message if not prior else f"{prior}\nuser: {message}"
        provider = get_provider(self.settings, "workhorse")
        return provider.complete(prompt, system=system)

    def remember(self, owner_id: str, turns) -> str:
        store = UserStore(self.conn, owner_id)
        transcript = _format_history(turns)
        summary_prompt = (
            "Summarize this conversation in two or three sentences. "
            "Capture any decisions and durable facts about the user. Be concise.\n\n" + transcript
        )
        provider = get_provider(self.settings, "workhorse")
        summary = provider.complete(summary_prompt)
        vec = self.embedder.embed(summary)
        store.add_episode(summary, vec)
        return summary
