import sys
from assistant.config import load_settings
from assistant.embeddings.ollama_embedder import OllamaEmbedder
from assistant.data.db import connect
from assistant.orchestrator.orchestrator import Orchestrator


def main():
    owner_id = sys.argv[1] if len(sys.argv) > 1 else None
    if not owner_id:
        print("usage: python -m assistant.chat <owner_id>")
        return

    settings = load_settings()
    embedder = OllamaEmbedder()
    conn = connect()
    orch = Orchestrator(conn, settings, embedder)

    history = []
    print("Chatting. Type 'exit' to end and save a memory.")
    while True:
        message = input("you: ").strip()
        if message.lower() in ("exit", "quit"):
            break
        if not message:
            continue
        answer = orch.respond(owner_id, message, history)
        print(f"assistant: {answer}")
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": answer})

    if history:
        summary = orch.remember(owner_id, history)
        print(f"[saved memory: {summary}]")


if __name__ == "__main__":
    main()
