import yaml
from pydantic import BaseModel


class ModelTier(BaseModel):
    provider: str
    model: str
    base_url: str = "http://localhost:11434"


class TranscriptionCfg(BaseModel):
    mode: str = "local"
    remote_url: str = "http://localhost:9000/transcribe"
    model_size: str = "large-v3"
    device: str = "cpu"
    compute_type: str = "int8"


class ResearchCfg(BaseModel):
    provider: str = "perplexity"
    model: str = "sonar"


class FinanceCfg(BaseModel):
    plaid_env: str = "sandbox"


class Settings(BaseModel):
    models: dict[str, ModelTier]
    transcription: TranscriptionCfg = TranscriptionCfg()
    timezone: str = "America/New_York"
    research: ResearchCfg = ResearchCfg()
    finance: FinanceCfg = FinanceCfg()
    charts_dir: str = "./charts"


def load_settings(path: str = "config.yaml") -> Settings:
    with open(path) as f:
        return Settings(**yaml.safe_load(f))
