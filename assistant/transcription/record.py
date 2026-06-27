import queue
import sounddevice as sd
import soundfile as sf
import numpy as np


def record_to_wav(path: str, samplerate: int = 16000) -> str:
    q: queue.Queue = queue.Queue()

    def callback(indata, frames, time, status):
        q.put(indata.copy())

    print("Recording. Press Enter to stop.")
    with sd.InputStream(samplerate=samplerate, channels=1, callback=callback):
        input()

    chunks = []
    while not q.empty():
        chunks.append(q.get())
    audio = np.concatenate(chunks, axis=0) if chunks else np.zeros((1, 1))
    sf.write(path, audio, samplerate)
    return path
