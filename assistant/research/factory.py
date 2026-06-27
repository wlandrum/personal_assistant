from assistant.config import Settings
from assistant.research.perplexity import PerplexityResearch


def get_research_provider(settings: Settings):
    cfg = settings.research
    if cfg.provider == "perplexity":
        return PerplexityResearch(cfg.model)
    raise ValueError(f"unknown research provider: {cfg.provider}")
