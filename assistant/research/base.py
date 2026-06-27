from typing import Protocol


class ResearchProvider(Protocol):
    def research(self, query: str) -> dict:
        # returns {"answer": str, "citations": list[str]}
        ...
