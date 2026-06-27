import os
import requests


def _parse(data: dict) -> dict:
    answer = data["choices"][0]["message"]["content"]
    citations = data.get("citations", [])
    return {"answer": answer, "citations": citations}


class PerplexityResearch:
    def __init__(self, model: str = "sonar"):
        self.model = model

    def research(self, query: str) -> dict:
        key = os.environ["PERPLEXITY_API_KEY"]
        resp = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "Be concise and factual, and cite your sources."},
                    {"role": "user", "content": query},
                ],
            },
            timeout=60,
        )
        resp.raise_for_status()
        return _parse(resp.json())
