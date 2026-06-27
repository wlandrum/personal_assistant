from typing import Protocol


class GmailClient(Protocol):
    def list_recent(self, max_results: int = 20) -> list[str]:
        ...

    def get_message(self, message_id: str) -> dict:
        ...
