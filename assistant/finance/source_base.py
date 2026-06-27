from typing import Protocol


class TransactionSource(Protocol):
    source_name: str

    def fetch(self) -> list[dict]:
        # each item: {"external_id": str, "date": "YYYY-MM-DD", "name": str, "amount": float}
        ...
