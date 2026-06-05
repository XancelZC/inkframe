"""LLM models API route."""

from __future__ import annotations

import os
import time
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.llm.registry import list_providers, get_provider

router = APIRouter(tags=["models"])

# Per-provider configuration
_provider_configs: dict[str, dict[str, str]] = {
    "mock": {"provider_id": "mock", "api_key": "", "base_url": "", "model": "mock-screenplay", "custom_models": ""},
    "openai_compatible": {"provider_id": "openai_compatible", "api_key": "", "base_url": "https://api.openai.com/v1", "model": "", "custom_models": ""},
    "anthropic": {"provider_id": "anthropic", "api_key": "", "base_url": "https://api.anthropic.com", "model": "", "custom_models": ""},
}

_active_provider = "mock"


@router.get("/models")
def get_models():
    """Return available LLM providers and models."""
    return list_providers()


@router.get("/models/config")
def get_model_config():
    """Return current LLM configuration for all providers."""
    result = {}
    for pid, cfg in _provider_configs.items():
        result[pid] = {
            "provider_id": pid,
            "base_url": cfg["base_url"],
            "model": cfg["model"],
            "has_api_key": bool(cfg["api_key"]),
            "custom_models": cfg["custom_models"],
        }
    result["active_provider"] = _active_provider
    return result


class ProviderConfigRequest(BaseModel):
    provider_id: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None
    custom_models: Optional[str] = None


@router.put("/models/config")
def update_provider_config(req: ProviderConfigRequest):
    """Update configuration for a specific provider."""
    if req.provider_id not in _provider_configs:
        return {"error": f"Unknown provider: {req.provider_id}"}

    cfg = _provider_configs[req.provider_id]

    if req.api_key is not None:
        cfg["api_key"] = req.api_key
        # Set environment variables
        if req.provider_id == "openai_compatible":
            os.environ["OPENAI_API_KEY"] = req.api_key
        elif req.provider_id == "anthropic":
            os.environ["ANTHROPIC_API_KEY"] = req.api_key

    if req.base_url is not None:
        cfg["base_url"] = req.base_url
        if req.provider_id == "openai_compatible":
            os.environ["OPENAI_BASE_URL"] = req.base_url
        elif req.provider_id == "anthropic":
            os.environ["ANTHROPIC_BASE_URL"] = req.base_url

    if req.model is not None:
        cfg["model"] = req.model

    if req.custom_models is not None:
        cfg["custom_models"] = req.custom_models

    return {"status": "saved", "provider_id": req.provider_id}


class SetActiveProviderRequest(BaseModel):
    provider_id: str


@router.put("/models/active")
def set_active_provider(req: SetActiveProviderRequest):
    """Set the active LLM provider."""
    global _active_provider
    if req.provider_id not in _provider_configs:
        return {"error": f"Unknown provider: {req.provider_id}"}
    _active_provider = req.provider_id
    return {"status": "ok", "active_provider": _active_provider}


@router.post("/models/test")
def test_connection(provider_id: str):
    """Test if the provider connection works."""
    provider = get_provider(provider_id)
    if provider is None:
        return {"success": False, "error": f"Unknown provider: {provider_id}"}

    cfg = _provider_configs.get(provider_id, {})

    # Set env vars for the test
    if provider_id == "openai_compatible":
        if cfg.get("api_key"):
            os.environ["OPENAI_API_KEY"] = cfg["api_key"]
        if cfg.get("base_url"):
            os.environ["OPENAI_BASE_URL"] = cfg["base_url"]
    elif provider_id == "anthropic":
        if cfg.get("api_key"):
            os.environ["ANTHROPIC_API_KEY"] = cfg["api_key"]
        if cfg.get("base_url"):
            os.environ["ANTHROPIC_BASE_URL"] = cfg["base_url"]

    try:
        start = time.time()
        result = provider.generate_json(
            "Return a JSON object with a single field 'status' set to 'ok'.",
            {"type": "object", "properties": {"status": {"type": "string"}}, "required": ["status"]},
        )
        elapsed = round(time.time() - start, 2)
        return {"success": True, "elapsed_seconds": elapsed, "response": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_active_provider_id() -> str:
    """Return the currently active provider ID."""
    return _active_provider


def get_active_model() -> str:
    """Return the currently active model name."""
    cfg = _provider_configs.get(_active_provider, {})
    return cfg.get("model", "")
