"""LLM models API route."""

from fastapi import APIRouter

from app.llm.registry import list_providers

router = APIRouter(tags=["models"])


@router.get("/models")
def get_models():
    """Return available LLM providers and models."""
    return list_providers()
