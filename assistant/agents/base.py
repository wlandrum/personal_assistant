from typing import Protocol, Union
from assistant.agents.actions import PendingAction


class Subagent(Protocol):
    name: str

    def handle(self, owner_id: str, message: str) -> Union[str, PendingAction]:
        ...
