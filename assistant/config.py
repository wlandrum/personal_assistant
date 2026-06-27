import yaml
from pydantic import BaseModel


class ModelTier(BaseModel):
    provider: str
    model: str
    base_url: str = "http://localhost:11434"


class Settings(BaseModel):
    models: dict[str, ModelTier]


def load_settings(path: str = "config.yaml") -> Settings:
    with open(path) as f:
        return Settings(**yaml.safe_load(f))
