from typing import Protocol


class LLMProvider(Protocol):
    def complete(self, prompt: str, system: str | None = None) -> str:
        ...
