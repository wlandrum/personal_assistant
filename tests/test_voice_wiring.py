from assistant.voice import process_voice


class FakeTranscriber:
    def transcribe(self, audio_path):
        return "need to call the vendor and prep the monday review"


class FakeOrch:
    def __init__(self):
        self.last_message = None

    def respond(self, owner_id, message, history=None):
        self.last_message = message
        return "ok"


def test_process_voice_passes_transcript_to_orchestrator():
    orch = FakeOrch()
    text, answer = process_voice(FakeTranscriber(), orch, "user-1", "ignored.wav")
    assert "vendor" in text
    assert orch.last_message == text
    assert answer == "ok"
