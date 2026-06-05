"""Anthropic-compatible LLM provider.

Environment variables:
- ANTHROPIC_API_KEY: API key
- ANTHROPIC_BASE_URL: Base URL (default: https://api.anthropic.com)
"""

from __future__ import annotations

import json
import os
from typing import Any, AsyncIterator

from app.llm.base import LLMProvider


class AnthropicProvider(LLMProvider):
    """Provider that works with Anthropic Claude API."""

    @property
    def provider_id(self) -> str:
        return "anthropic"

    def list_models(self) -> list[str]:
        return []  # 不预设模型，通过 fetch 获取

    def generate_json(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        """Send a message and parse JSON response."""
        try:
            from anthropic import Anthropic
        except ImportError:
            raise RuntimeError("anthropic package not installed. Run: pip install anthropic")

        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        base_url = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com")

        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        client = Anthropic(api_key=api_key, base_url=base_url)

        system_prompt = (
            "你是一个专业的中文剧本分析助手。"
            "所有输出内容必须使用中文（包括对话、动作描述、旁白等）。"
            "只返回符合要求的 JSON，不要包含任何其他文字。"
        )

        model = os.environ.get("ANTHROPIC_MODEL", "") or "claude-sonnet-4-20250514"

        try:
            response = client.messages.create(
                model=model,
                max_tokens=4096,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": f"{prompt}\n\nSchema:\n{json.dumps(schema, indent=2)}"},
                ],
            )
        except Exception as e:
            error_msg = str(e).lower()
            if "rate" in error_msg or "429" in error_msg:
                raise RuntimeError(f"rate_limited: {e}") from e
            elif "timeout" in error_msg:
                raise RuntimeError(f"timeout: {e}") from e
            else:
                raise RuntimeError(f"provider_error: {e}") from e

        content = response.content[0].text if response.content else ""
        if not content:
            raise ValueError("Empty response from LLM")

        # Extract JSON from response (may be wrapped in ```json ... ```)
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"invalid_json: {e}") from e

    async def stream_json(
        self, prompt: str, schema: dict[str, Any]
    ) -> AsyncIterator[dict[str, Any]]:
        """Stream partial JSON results."""
        try:
            from anthropic import AsyncAnthropic
        except ImportError:
            raise RuntimeError("anthropic package not installed")

        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        base_url = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com")

        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")

        client = AsyncAnthropic(api_key=api_key, base_url=base_url)

        system_prompt = (
            "你是一个专业的中文剧本分析助手。"
            "所有输出内容必须使用中文。"
            "只返回符合要求的 JSON，不要包含任何其他文字。"
        )

        model = os.environ.get("ANTHROPIC_MODEL", "") or "claude-sonnet-4-20250514"

        try:
            accumulated = ""
            with client.messages.stream(
                model=model,
                max_tokens=4096,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": f"{prompt}\n\nSchema:\n{json.dumps(schema, indent=2)}"},
                ],
            ) as stream:
                for text in stream.text_stream:
                    accumulated += text
                    try:
                        yield json.loads(accumulated)
                    except json.JSONDecodeError:
                        pass
        except Exception as e:
            error_msg = str(e).lower()
            if "rate" in error_msg or "429" in error_msg:
                raise RuntimeError(f"rate_limited: {e}") from e
            else:
                raise RuntimeError(f"provider_error: {e}") from e
