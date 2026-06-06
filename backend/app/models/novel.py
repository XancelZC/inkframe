"""Novel (folder) structures.

A novel groups multiple chapters (projects) together.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

from app.models.ids import ProjectId


def _make_novel_id() -> str:
    """Generate a novel ID: nvl_<8hex>."""
    import uuid
    return f"nvl_{uuid.uuid4().hex[:8]}"


class NovelSummary(BaseModel):
    """Summary for the novel list."""

    id: str = Field(default_factory=_make_novel_id)
    title: str
    language: str = "zh"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class NovelIndex(BaseModel):
    """The novels index file."""

    novels: list[NovelSummary] = Field(default_factory=list)
