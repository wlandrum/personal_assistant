import pytest
from assistant.config import Settings, OllamaCfg, ClaudeCfg
from assistant.llm.factory import get_provider
from assistant.llm.ollama_provider import OllamaProvider


def test_factory_returns_ollama():
    s = Settings(provider="ollama", ollama=OllamaCfg(model="gemma3:4b"))
    p = get_provider(s)
    assert isinstance(p, OllamaProvider)
    assert p.model == "gemma3:4b"


def test_factory_unknown_provider_raises():
    s = Settings(provider="nope")
    with pytest.raises(ValueError):
        get_provider(s)
