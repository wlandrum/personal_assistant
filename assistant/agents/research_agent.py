from assistant.data.store import UserStore
from assistant.research.factory import get_research_provider


class ResearchSubagent:
    name = "research"

    def __init__(self, conn, settings, embedder=None):
        self.conn = conn
        self.settings = settings

    def handle(self, owner_id: str, message: str) -> str:
        provider = get_research_provider(self.settings)
        result = provider.research(message)

        UserStore(self.conn, owner_id).add_audit("research", message[:200])

        lines = [result["answer"]]
        if result.get("citations"):
            lines.append("")
            lines.append("Sources:")
            for i, url in enumerate(result["citations"], 1):
                lines.append(f"{i}. {url}")
        return "\n".join(lines)
