import os
import tempfile
from fastapi import FastAPI, UploadFile, File
from assistant.config import load_settings
from assistant.transcription.whisper_transcriber import FasterWhisperTranscriber

settings = load_settings()
t = settings.transcription
_model = FasterWhisperTranscriber(t.model_size, t.device, t.compute_type)

app = FastAPI()


@app.post("/transcribe")
def transcribe(file: UploadFile = File(...)):
    path = os.path.join(tempfile.gettempdir(), "remote_voice.wav")
    with open(path, "wb") as f:
        f.write(file.file.read())
    return {"transcript": _model.transcribe(path)}
