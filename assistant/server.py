import os
import hashlib
import tempfile
from threading import Lock

from fastapi import FastAPI, Depends, HTTPException, Header, UploadFile, File
from fastapi.staticfiles import StaticFiles

from assistant.config import load_settings
from assistant.embeddings.ollama_embedder import OllamaEmbedder
from assistant.data.db import connect, apply_schema
from assistant.orchestrator.orchestrator import Orchestrator
from assistant.transcription.factory import get_transcriber

settings = load_settings()
conn = connect()
apply_schema(conn)
embedder = OllamaEmbedder(base_url=settings.models["router"].base_url)
orch = Orchestrator(conn, settings, embedder)

_lock = Lock()
_transcriber = None


app = FastAPI()


def resolve_owner(authorization: str = Header(default=None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing bearer token")
    token = authorization.split(" ", 1)[1]
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    with _lock:
        cur = conn.execute("SELECT owner_id FROM api_tokens WHERE token_hash = %s", (token_hash,))
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="invalid token")
    return str(row[0])


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/message")
def message(body: dict, owner_id: str = Depends(resolve_owner)):
    text = (body or {}).get("message", "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="empty message")
    with _lock:
        reply = orch.respond(owner_id, text)
    return {"reply": reply}


def _get_transcriber():
    global _transcriber
    if _transcriber is None:
        _transcriber = get_transcriber(settings)
    return _transcriber


@app.post("/voice")
def voice(file: UploadFile = File(...), owner_id: str = Depends(resolve_owner)):
    path = os.path.join(tempfile.gettempdir(), "upload_voice.wav")
    with open(path, "wb") as f:
        f.write(file.file.read())
    transcript = _get_transcriber().transcribe(path)
    with _lock:
        reply = orch.respond(owner_id, transcript)
    return {"transcript": transcript, "reply": reply}


app.mount("/", StaticFiles(directory="assistant/static", html=True), name="static")
