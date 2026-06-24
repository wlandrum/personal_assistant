from anthropic import Anthropic


class ClaudeProvider:
    def __init__(self, model: str):
        self.client = Anthropic()   # reads ANTHROPIC_API_KEY from env
        self.model = model

    def complete(self, prompt: str, system: str | None = None) -> str:
        msg = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=system or "",
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text
