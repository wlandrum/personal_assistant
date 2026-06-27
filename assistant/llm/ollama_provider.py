import ollama


class OllamaProvider:
    def __init__(self, base_url: str, model: str):
        self.client = ollama.Client(host=base_url)
        self.model = model

    def complete(self, prompt: str, system: str | None = None) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        resp = self.client.chat(model=self.model, messages=messages)
        return resp["message"]["content"]
