# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup

Copy `.env.example` to `.env` and fill in your `ANTHROPIC_API_KEY` before using the Claude provider.

Install dependencies (from the project root):
```
pip install -r requirements.txt
```

## Commands

Run the smoke test (sends a prompt to the configured provider):
```
python -m assistant.smoke [optional prompt text]
```

Run all tests:
```
pytest
```

Run a single test:
```
pytest tests/test_factory.py::test_factory_returns_ollama
```

## Architecture

The project is a thin LLM abstraction layer with two pluggable backends.

**Config layer** (`assistant/config.py`): `load_settings()` reads `config.yaml` and returns a `Settings` Pydantic model. The top-level `provider` field (`"ollama"` or `"claude"`) selects which backend is active.

**Provider protocol** (`assistant/llm/base.py`): All providers satisfy the `LLMProvider` protocol — a single `complete(prompt, system=None) -> str` method.

**Factory** (`assistant/llm/factory.py`): `get_provider(settings)` instantiates and returns the correct provider. Adding a new provider means adding a branch here and a corresponding config block in `Settings`.

**Providers**:
- `OllamaProvider` — talks to a local Ollama server (`base_url` from config, defaults to `http://localhost:11434`)
- `ClaudeProvider` — uses the Anthropic SDK; picks up `ANTHROPIC_API_KEY` from the environment automatically

**Entry point** (`assistant/smoke.py`): `main()` loads settings, builds the provider, and calls `complete()` on a prompt from `sys.argv`. Run with `python -m assistant.smoke`.

## Config

`config.yaml` controls which provider and model are used at runtime. The acceptance test overrides the Ollama model to `gemma3:4b` for speed; production default is `qwen3.6:27b`. Switch providers by changing the `provider` key to `ollama` or `claude`.
