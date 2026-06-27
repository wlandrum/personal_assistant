from typing import Protocol


class CalendarClient(Protocol):
    def create_event(self, title: str, start_iso: str, end_iso: str,
                     timezone: str, description: str | None = None) -> str:
        ...
