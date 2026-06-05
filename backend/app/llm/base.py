"""Abstract LLM provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator


class LLMProvider(ABC):
    """Base class for LLM providers."""

    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Unique identifier for this provider."""

    @abstractmethod
    def list_models(self) -> list[str]:
        """Return available model names."""

    @abstractmethod
    def generate_json(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        """Send a prompt and return JSON matching the given schema."""

    @abstractmethod
    async def stream_json(
        self, prompt: str, schema: dict[str, Any]
    ) -> AsyncIterator[dict[str, Any]]:
        """Stream partial JSON results matching the given schema."""
