import yaml
from pydantic import BaseModel


class OllamaCfg(BaseModel):
    base_url: str = "http://localhost:11434"
    model: str = "qwen3.6:27b"


class ClaudeCfg(BaseModel):
    model: str = "claude-sonnet-4-6"


class Settings(BaseModel):
    provider: str = "ollama"
    ollama: OllamaCfg = OllamaCfg()
    claude: ClaudeCfg = ClaudeCfg()


def load_settings(path: str = "config.yaml") -> Settings:
    with open(path) as f:
        return Settings(**yaml.safe_load(f))
