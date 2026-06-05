"""Mock LLM provider for development and testing.

Returns deterministic JSON responses based on the schema.
No API key required.
"""

from __future__ import annotations

import json
from typing import Any, AsyncIterator

from app.llm.base import LLMProvider


def _generate_mock_value(schema: dict[str, Any], key: str = "") -> Any:
    """Generate a deterministic mock value based on JSON schema type."""
    schema_type = schema.get("type", "string")

    if schema_type == "string":
        if "enum" in schema:
            return schema["enum"][0]
        return f"mock_{key}" if key else "mock_value"
    elif schema_type == "integer":
        return 1
    elif schema_type == "number":
        return 0.5
    elif schema_type == "boolean":
        return True
    elif schema_type == "array":
        items = schema.get("items", {"type": "string"})
        return [_generate_mock_value(items, key)]
    elif schema_type == "object":
        properties = schema.get("properties", {})
        result = {}
        for prop_key, prop_schema in properties.items():
            result[prop_key] = _generate_mock_value(prop_schema, prop_key)
        return result
    else:
        return f"mock_{key}" if key else "mock_value"


class MockProvider(LLMProvider):
    """Mock provider that returns deterministic JSON."""

    @property
    def provider_id(self) -> str:
        return "mock"

    def list_models(self) -> list[str]:
        return ["mock-screenplay"]

    def generate_json(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        return _generate_mock_value(schema)

    async def stream_json(
        self, prompt: str, schema: dict[str, Any]
    ) -> AsyncIterator[dict[str, Any]]:
        result = _generate_mock_value(schema)
        yield result
