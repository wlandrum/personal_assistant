from typing import Protocol


class Transcriber(Protocol):
    def transcribe(self, audio_path: str) -> str:
        ...
