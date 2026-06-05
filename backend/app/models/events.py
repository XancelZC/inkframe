"""SSE event structure for pipeline progress.

From PRD section "Progress and Async Processing" — event structure.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from app.models.ids import ChapterId, ProjectId
from app.models.status import PipelineStage, StatusEnum


class SSEEvent(BaseModel):
    """Server-Sent Event for pipeline progress."""

    project_id: ProjectId
    stage: PipelineStage
    status: StatusEnum
    chapter_id: Optional[ChapterId] = None
    progress: float = Field(default=0.0, ge=0.0, le=1.0)
    message: str = ""
