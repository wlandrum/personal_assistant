import yaml
from pydantic import BaseModel


class ModelTier(BaseModel):
    provider: str
    model: str
    base_url: str = "http://localhost:11434"


class TranscriptionCfg(BaseModel):
    model_size: str = "large-v3"
    device: str = "cuda"
    compute_type: str = "float16"


class Settings(BaseModel):
    models: dict[str, ModelTier]
    transcription: TranscriptionCfg = TranscriptionCfg()


def load_settings(path: str = "config.yaml") -> Settings:
    with open(path) as f:
        return Settings(**yaml.safe_load(f))
