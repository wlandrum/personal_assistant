from assistant.data.store import UserStore
from assistant.orchestrator.context import build_context
from assistant.llm.factory import get_provider
from assistant.agents.router import classify
from assistant.agents.notes import NotesSubagent
from assistant.agents.calendar import CalendarSubagent
from assistant.agents.email import EmailSubagent
from assistant.agents.research_agent import ResearchSubagent
from assistant.agents.coding import CodingSubagent
from assistant.agents.critic import CriticSubagent
from assistant.agents.actions import PendingAction


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
            "calendar": CalendarSubagent(conn, settings, embedder),
            "email": EmailSubagent(conn, settings, embedder),
            "research": ResearchSubagent(conn, settings, embedder),
            "code": CodingSubagent(conn, settings, embedder),
        }
        self.pending = {}
        self.critic = CriticSubagent(conn, settings, embedder)
        self.critiques = {}

    def respond(self, owner_id: str, message: str, history=None) -> str:
        pending = self.pending.get(owner_id)
        if pending is not None:
            decision = message.strip().lower()
            if decision in ("confirm", "yes", "y", "ok", "do it"):
                self.pending.pop(owner_id, None)
                return pending.execute()
            if decision in ("cancel", "no", "n", "stop"):
                self.pending.pop(owner_id, None)
                return "Cancelled. Nothing was written."
            return f"You have a pending action:\n{pending.summary}\nReply 'confirm' or 'cancel'."

        # active critique discussion
        session = self.critiques.get(owner_id)
        if session is not None:
            verdict = self.critic.detect_terminal(message)
            if verdict in ("accept", "reject"):
                summary = self.critic.resolve(owner_id, session["idea"], session["history"], verdict)
                self.critiques.pop(owner_id, None)
                return summary
            reply = self.critic.round(owner_id, message, session["history"])
            session["history"].append({"role": "user", "content": message})
            session["history"].append({"role": "assistant", "content": reply})
            return reply

        router_provider = get_provider(self.settings, "router")
        route = classify(router_provider, message)

        if route == "critic":
            opening = self.critic.open(owner_id, message)
            self.critiques[owner_id] = {
                "idea": message,
                "history": [
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": opening},
                ],
            }
            return opening + "\n\nLet us talk it through. Share your thoughts, or say you accept or reject it to conclude."

        if route in self.subagents:
            result = self.subagents[route].handle(owner_id, message)
            if isinstance(result, PendingAction):
                self.pending[owner_id] = result
                return f"{result.summary}\nReply 'confirm' to proceed or 'cancel' to discard."
            return result

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
