"""OpenAI-compatible LLM provider.

Works with OpenAI API directly and any OpenAI-compatible endpoint
(e.g., domestic model providers).

Environment variables:
- OPENAI_API_KEY: API key
- OPENAI_BASE_URL: Base URL (default: https://api.openai.com/v1)
"""

from __future__ import annotations

import json
import os
from typing import Any, AsyncIterator

from app.llm.base import LLMProvider


class OpenAICompatibleProvider(LLMProvider):
    """Provider that works with OpenAI-compatible APIs."""

    @property
    def provider_id(self) -> str:
        return "openai_compatible"

    def list_models(self) -> list[str]:
        return []  # 不预设模型，通过 fetch 从 API 获取

    def generate_json(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        """Send a chat completion request and parse JSON response."""
        try:
            from openai import OpenAI
        except ImportError:
            raise RuntimeError("openai package not installed. Run: pip install openai")

        api_key = os.environ.get("OPENAI_API_KEY", "")
        base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")

        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        client = OpenAI(api_key=api_key, base_url=base_url)

        system_prompt = (
            "你是一个专业的中文剧本分析助手。"
            "所有输出内容必须使用中文（包括对话、动作描述、旁白等）。"
            "只返回符合要求的 JSON，不要包含任何其他文字。"
        )

        model = os.environ.get("OPENAI_MODEL", "") or "gpt-4o-mini"

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"{prompt}\n\nSchema:\n{json.dumps(schema, indent=2)}"},
                ],
                temperature=0.3,
                response_format={"type": "json_object"},
            )
        except Exception as e:
            error_msg = str(e).lower()
            if "rate" in error_msg or "429" in error_msg:
                raise RuntimeError(f"rate_limited: {e}") from e
            elif "timeout" in error_msg:
                raise RuntimeError(f"timeout: {e}") from e
            else:
                raise RuntimeError(f"provider_error: {e}") from e

        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from LLM")

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"invalid_json: {e}") from e

    async def stream_json(
        self, prompt: str, schema: dict[str, Any]
    ) -> AsyncIterator[dict[str, Any]]:
        """Stream partial JSON results."""
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise RuntimeError("openai package not installed")

        api_key = os.environ.get("OPENAI_API_KEY", "")
        base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")

        if not api_key:
            raise ValueError("OPENAI_API_KEY not set")

        client = AsyncOpenAI(api_key=api_key, base_url=base_url)

        system_prompt = (
            "你是一个专业的中文剧本分析助手。"
            "所有输出内容必须使用中文。"
            "只返回符合要求的 JSON，不要包含任何其他文字。"
        )

        model = os.environ.get("OPENAI_MODEL", "") or "gpt-4o-mini"

        try:
            stream = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"{prompt}\n\nSchema:\n{json.dumps(schema, indent=2)}"},
                ],
                temperature=0.3,
                stream=True,
            )

            accumulated = ""
            async for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                accumulated += delta
                # Try to parse accumulated JSON
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
