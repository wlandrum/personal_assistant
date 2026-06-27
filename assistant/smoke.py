import sys
from .config import load_settings
from .llm.factory import get_provider


def main():
    settings = load_settings()
    provider = get_provider(settings)
    prompt = " ".join(sys.argv[1:]) or "Say hello in one short sentence."
    active = getattr(settings, settings.provider)
    print(f"[provider={settings.provider} model={active.model}]")
    print(provider.complete(prompt))


if __name__ == "__main__":
    main()
