from assistant.data.store import UserStore
from assistant.llm.escalation import provider_for

CRITIC_SYSTEM = (
    "You are a rigorous, honest thinking partner. Your job is to test ideas, not to flatter. "
    "First briefly steelman the idea in its strongest form. Then give your most important "
    "objections, name the assumptions it depends on, and point out where it is weakest. "
    "Concede what is genuinely strong. Be direct and specific. You are willing to conclude that "
    "an idea should be rejected. The goal is the truth of the idea, not the user's comfort."
)

OVERRIDE_PHRASES = ("think hard", "use claude", "[hard]")


def _format(history):
    return "\n".join(f"{t['role']}: {t['content']}" for t in history)


class CriticSubagent:
    def __init__(self, conn, settings, embedder):
        self.conn = conn
        self.settings = settings
        self.embedder = embedder

    def _want_frontier(self, text: str) -> bool:
        lowered = text.lower()
        return any(p in lowered for p in OVERRIDE_PHRASES)

    def open(self, owner_id: str, idea: str) -> str:
        provider, _tier, note = provider_for(self.settings, self._want_frontier(idea))
        prompt = (
            "The user proposes this idea. Steelman it briefly, then give your strongest objections "
            "and the key assumptions it rests on.\n\nIdea:\n" + idea
        )
        return note + provider.complete(prompt, system=CRITIC_SYSTEM)

    def detect_terminal(self, message: str) -> str:
        small = __import__("assistant.llm.factory", fromlist=["get_provider"]).get_provider(self.settings, "router")
        prompt = (
            "In a discussion about an idea, is the user concluding with a decision now? "
            "Answer one word: accept if they are deciding to go ahead, reject if they are deciding against, "
            "or continue if they are still discussing.\n\nMessage:\n" + message
        )
        verdict = small.complete(prompt).strip().lower()
        if "accept" in verdict:
            return "accept"
        if "reject" in verdict:
            return "reject"
        return "continue"

    def round(self, owner_id: str, message: str, history) -> str:
        provider, _tier, note = provider_for(self.settings, self._want_frontier(message))
        prompt = (
            "Continue the critical discussion below. Engage with the user's latest response, "
            "concede what is valid, and press where the idea is still weak.\n\n"
            + _format(history) + f"\nuser: {message}"
        )
        return note + provider.complete(prompt, system=CRITIC_SYSTEM)

    def resolve(self, owner_id: str, idea: str, history, verdict: str) -> str:
        provider, _tier, _note = provider_for(self.settings, False)
        prompt = (
            f"The discussion has concluded with the user choosing to {verdict} this idea. "
            "Write a short summary: the idea, the verdict, and the two or three key reasons. "
            "Be concise and neutral.\n\nIdea:\n" + idea + "\n\nDiscussion:\n" + _format(history)
        )
        reasoning = provider.complete(prompt, system=CRITIC_SYSTEM)

        store = UserStore(self.conn, owner_id)
        store.add_decision(idea, verdict, reasoning)
        episode = f"Decision ({verdict}): {idea}. Reasoning: {reasoning}"
        store.add_episode(episode, self.embedder.embed(episode))
        store.add_audit("decision", f"{verdict}: {idea[:120]}")

        return f"Recorded as {verdict}.\n\n{reasoning}"
