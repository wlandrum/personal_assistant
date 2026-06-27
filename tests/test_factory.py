import pytest
from assistant.config import Settings, ModelTier
from assistant.llm.factory import get_provider
from assistant.llm.ollama_provider import OllamaProvider


def test_factory_returns_ollama():
    s = Settings(models={"workhorse": ModelTier(provider="ollama", model="gemma3:4b")})
    p = get_provider(s, "workhorse")
    assert isinstance(p, OllamaProvider)
    assert p.model == "gemma3:4b"


def test_factory_unknown_tier_raises():
    s = Settings(models={"workhorse": ModelTier(provider="ollama", model="gemma3:4b")})
    with pytest.raises(ValueError):
        get_provider(s, "nope")
