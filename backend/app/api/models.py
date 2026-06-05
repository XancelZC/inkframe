"""LLM models API route."""

from __future__ import annotations

import os
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.llm.registry import list_providers, get_provider

router = APIRouter(tags=["models"])


# In-memory config (MVP; persists only while server is running)
_provider_config: dict[str, str] = {
    "provider_id": "mock",
    "api_key": "",
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-4o-mini",
}


@router.get("/models")
def get_models():
    """Return available LLM providers and models."""
    return list_providers()


@router.get("/models/config")
def get_model_config():
    """Return current LLM configuration."""
    return {
        "provider_id": _provider_config["provider_id"],
        "base_url": _provider_config["base_url"],
        "model": _provider_config["model"],
        "has_api_key": bool(_provider_config["api_key"]),
    }


class ModelConfigRequest(BaseModel):
    provider_id: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None


@router.put("/models/config")
def update_model_config(req: ModelConfigRequest):
    """Update LLM configuration."""
    if req.provider_id is not None:
        provider = get_provider(req.provider_id)
        if provider is None:
            return {"error": f"Unknown provider: {req.provider_id}"}
        _provider_config["provider_id"] = req.provider_id

    if req.api_key is not None:
        _provider_config["api_key"] = req.api_key
        os.environ["OPENAI_API_KEY"] = req.api_key

    if req.base_url is not None:
        _provider_config["base_url"] = req.base_url
        os.environ["OPENAI_BASE_URL"] = req.base_url

    if req.model is not None:
        _provider_config["model"] = req.model

    return {"status": "saved", **get_model_config()}


def get_active_provider_id() -> str:
    """Return the currently active provider ID."""
    return _provider_config["provider_id"]


def get_active_model() -> str:
    """Return the currently active model name."""
    return _provider_config["model"]
