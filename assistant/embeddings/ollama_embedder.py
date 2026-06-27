import ollama


class OllamaEmbedder:
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "nomic-embed-text"):
        self.client = ollama.Client(host=base_url)
        self.model = model

    def embed(self, text: str) -> list[float]:
        resp = self.client.embeddings(model=self.model, prompt=text)
        return resp["embedding"]
