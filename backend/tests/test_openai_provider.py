"""Tests for Issue #13: OpenAI-compatible provider."""

import os
import pytest
from unittest.mock import patch, MagicMock

from app.llm.openai_compat import OpenAICompatibleProvider


class TestOpenAIProvider:
    def test_provider_id(self):
        p = OpenAICompatibleProvider()
        assert p.provider_id == "openai_compatible"

    def test_list_models(self):
        p = OpenAICompatibleProvider()
        models = p.list_models()
        assert isinstance(models, list)
        # 不预设模型，通过 fetch 从 API 获取

    def test_generate_json_requires_api_key(self):
        p = OpenAICompatibleProvider()
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
            with pytest.raises(ValueError, match="OPENAI_API_KEY"):
                p.generate_json("test", {"type": "object"})

    def test_generate_json_with_mock_openai(self):
        p = OpenAICompatibleProvider()

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"characters": [{"name": "Tom"}]}'

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch("openai.OpenAI") as mock_openai:
                mock_client = MagicMock()
                mock_client.chat.completions.create.return_value = mock_response
                mock_openai.return_value = mock_client

                result = p.generate_json("extract characters", {"type": "object"})
                assert "characters" in result
                mock_client.chat.completions.create.assert_called_once()

    def test_generate_json_handles_rate_limit(self):
        p = OpenAICompatibleProvider()

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch("openai.OpenAI") as mock_openai:
                mock_client = MagicMock()
                mock_client.chat.completions.create.side_effect = Exception("Rate limit exceeded (429)")
                mock_openai.return_value = mock_client

                with pytest.raises(RuntimeError, match="rate_limited"):
                    p.generate_json("test", {"type": "object"})

    def test_generate_json_handles_timeout(self):
        p = OpenAICompatibleProvider()

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch("openai.OpenAI") as mock_openai:
                mock_client = MagicMock()
                mock_client.chat.completions.create.side_effect = Exception("Request timeout")
                mock_openai.return_value = mock_client

                with pytest.raises(RuntimeError, match="timeout"):
                    p.generate_json("test", {"type": "object"})

    def test_generate_json_handles_invalid_json(self):
        p = OpenAICompatibleProvider()

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "not valid json"

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch("openai.OpenAI") as mock_openai:
                mock_client = MagicMock()
                mock_client.chat.completions.create.return_value = mock_response
                mock_openai.return_value = mock_client

                with pytest.raises(ValueError, match="invalid_json"):
                    p.generate_json("test", {"type": "object"})
