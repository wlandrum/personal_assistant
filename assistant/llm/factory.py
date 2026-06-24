from ..config import Settings
from .ollama_provider import OllamaProvider
from .claude_provider import ClaudeProvider


def get_provider(settings: Settings):
    if settings.provider == "ollama":
        return OllamaProvider(settings.ollama.base_url, settings.ollama.model)
    if settings.provider == "claude":
        return ClaudeProvider(settings.claude.model)
    raise ValueError(f"unknown provider: {settings.provider}")
