"""Validation log structures.

From PRD Stage 3 — Consistency Validation output.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel

from app.models.ids import ElementId, SceneId


class ValidationSeverity(str, Enum):
    """Severity level for validation log entries."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationLogEntry(BaseModel):
    """A single entry in the validation log."""

    severity: ValidationSeverity
    code: str
    message: str
    scene_id: Optional[SceneId] = None
    element_id: Optional[ElementId] = None


class ValidationLog(BaseModel):
    """Stage 3 output: validation results.

    Persisted to validation_log.json.
    """

    entries: list[ValidationLogEntry] = []
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0
