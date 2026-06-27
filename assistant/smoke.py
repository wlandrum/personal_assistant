import sys
from .config import load_settings
from .llm.factory import get_provider


def main():
    settings = load_settings()
    tier = "workhorse"
    provider = get_provider(settings, tier)
    prompt = " ".join(sys.argv[1:]) or "Say hello in one short sentence."
    print(f"[tier={tier} model={settings.models[tier].model}]")
    print(provider.complete(prompt))


if __name__ == "__main__":
    main()
