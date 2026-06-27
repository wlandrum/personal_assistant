from typing import Protocol


class Subagent(Protocol):
    name: str

    def handle(self, owner_id: str, message: str) -> str:
        ...
