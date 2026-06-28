from assistant.transcription.remote_transcriber import RemoteTranscriber


class FakeResp:
    def raise_for_status(self):
        pass

    def json(self):
        return {"transcript": "hello world"}


def test_remote_transcriber_parses(monkeypatch, tmp_path):
    audio = tmp_path / "a.wav"
    audio.write_bytes(b"fake")
    monkeypatch.setattr(
        "assistant.transcription.remote_transcriber.requests.post",
        lambda url, files, timeout: FakeResp(),
    )
    rt = RemoteTranscriber("http://x/transcribe")
    assert rt.transcribe(str(audio)) == "hello world"
