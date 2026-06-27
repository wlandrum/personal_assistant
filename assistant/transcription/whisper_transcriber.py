from faster_whisper import WhisperModel


class FasterWhisperTranscriber:
    def __init__(self, model_size: str = "large-v3", device: str = "cuda", compute_type: str = "float16"):
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def transcribe(self, audio_path: str) -> str:
        segments, _info = self.model.transcribe(audio_path)
        return " ".join(seg.text.strip() for seg in segments).strip()
