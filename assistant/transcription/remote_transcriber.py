import requests


class RemoteTranscriber:
    def __init__(self, url: str):
        self.url = url

    def transcribe(self, audio_path: str) -> str:
        with open(audio_path, "rb") as f:
            resp = requests.post(self.url, files={"file": f}, timeout=120)
        resp.raise_for_status()
        return resp.json()["transcript"]
