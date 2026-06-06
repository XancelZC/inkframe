"""Project structures.

Project metadata and index for the file-backed storage.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

from app.models.ids import ProjectId


class ProjectSummary(BaseModel):
    """Summary stored in index.json for the project list."""

    id: ProjectId
    novel_id: Optional[str] = None  # 所属小说 ID，None 表示独立项目
    title: str
    source_language: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ProjectIndex(BaseModel):
    """The index.json file that stores all project summaries."""

    projects: list[ProjectSummary] = Field(default_factory=list)


class ProjectDetail(BaseModel):
    """Full project detail returned by GET /api/projects/{id}."""

    id: ProjectId
    novel_id: Optional[str] = None
    title: str
    source_language: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    raw_text: Optional[str] = None
