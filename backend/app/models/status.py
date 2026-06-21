"""Pipeline status and stage definitions.

Status enum and stage names from PRD section "Progress and Async Processing".
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class StatusEnum(str, Enum):
    """Pipeline run status."""

    IDLE = "idle"
    QUEUED = "queued"
    RUNNING = "running"
    STAGE_COMPLETED = "stage_completed"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PipelineStage(str, Enum):
    """Pipeline stage names."""

    PREPROCESSING = "preprocessing"
    CHARACTER_EXTRACTION = "character_extraction"
    SCENE_SYNTHESIS = "scene_synthesis"
    VALIDATION = "validation"
    YAML_FORMATTING = "yaml_formatting"


class PipelineStatus(BaseModel):
    """Status of a pipeline run, persisted to status.json."""

    project_id: str
    current_stage: Optional[PipelineStage] = None
    status: StatusEnum = StatusEnum.IDLE
    progress: float = Field(default=0.0, ge=0.0, le=1.0)
    error: Optional[str] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
