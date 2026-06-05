"""Provider registry."""

from __future__ import annotations

from typing import Optional

from app.llm.base import LLMProvider
from app.llm.mock import MockProvider

_PROVIDERS: dict[str, LLMProvider] = {
    "mock": MockProvider(),
}


def get_provider(provider_id: str) -> Optional[LLMProvider]:
    """Get a provider by ID."""
    return _PROVIDERS.get(provider_id)


def list_providers() -> list[dict[str, object]]:
    """Return all available providers and their models."""
    return [
        {"provider_id": p.provider_id, "models": p.list_models()}
        for p in _PROVIDERS.values()
    ]
