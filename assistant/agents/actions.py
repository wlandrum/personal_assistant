from dataclasses import dataclass
from typing import Callable


@dataclass
class PendingAction:
    summary: str
    execute: Callable[[], str]
