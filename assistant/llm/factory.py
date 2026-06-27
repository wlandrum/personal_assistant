from ..config import Settings
from .ollama_provider import OllamaProvider
from .claude_provider import ClaudeProvider


def get_provider(settings: Settings, tier: str = "workhorse"):
    if tier not in settings.models:
        raise ValueError(f"unknown model tier: {tier}")
    cfg = settings.models[tier]
    if cfg.provider == "ollama":
        return OllamaProvider(cfg.base_url, cfg.model)
    if cfg.provider == "claude":
        return ClaudeProvider(cfg.model)
    raise ValueError(f"unknown provider: {cfg.provider}")
