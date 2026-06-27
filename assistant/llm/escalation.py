import os
from assistant.llm.factory import get_provider


def provider_for(settings, want_frontier: bool):
    tier = "frontier" if want_frontier else "workhorse"
    note = ""
    if tier == "frontier" and not os.environ.get("ANTHROPIC_API_KEY"):
        tier = "workhorse"
        note = "(Claude was selected but no API key is set, so the local model answered instead.)\n\n"
    return get_provider(settings, tier), tier, note
