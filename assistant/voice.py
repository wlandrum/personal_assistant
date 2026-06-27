import sys
import tempfile
import os

from assistant.config import load_settings
from assistant.embeddings.ollama_embedder import OllamaEmbedder
from assistant.data.db import connect
from assistant.orchestrator.orchestrator import Orchestrator
from assistant.transcription.whisper_transcriber import FasterWhisperTranscriber
from assistant.transcription.record import record_to_wav


def process_voice(transcriber, orch, owner_id: str, audio_path: str):
    text = transcriber.transcribe(audio_path)
    answer = orch.respond(owner_id, text)
    return text, answer


def main():
    owner_id = sys.argv[1] if len(sys.argv) > 1 else None
    if not owner_id:
        print("usage: python -m assistant.voice <owner_id>")
        return

    settings = load_settings()
    embedder = OllamaEmbedder()
    conn = connect()
    orch = Orchestrator(conn, settings, embedder)
    transcriber = FasterWhisperTranscriber(
        settings.transcription.model_size,
        settings.transcription.device,
        settings.transcription.compute_type,
    )

    tmp = os.path.join(tempfile.gettempdir(), "voice_capture.wav")
    record_to_wav(tmp)
    text, answer = process_voice(transcriber, orch, owner_id, tmp)

    print(f"\ntranscript: {text}\n")
    print(f"assistant: {answer}")

    orch.remember(owner_id, [
        {"role": "user", "content": text},
        {"role": "assistant", "content": answer},
    ])


if __name__ == "__main__":
    main()
