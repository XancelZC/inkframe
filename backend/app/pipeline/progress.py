"""Pipeline progress tracking and SSE events.

Writes status.json during pipeline runs and provides
an async event stream for the frontend.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncIterator

from app.models.status import PipelineStatus, PipelineStage, StatusEnum
from app.models.events import SSEEvent
from app.storage import get_project_dir


class ProgressTracker:
    """Tracks pipeline progress and emits SSE events."""

    def __init__(self, project_id: str) -> None:
        self.project_id = project_id
        self._events: list[SSEEvent] = []
        self._status = PipelineStatus(project_id=project_id)
        self._save()

    def _save(self) -> None:
        """Persist status to status.json."""
        status_file = get_project_dir(self.project_id) / "status.json"
        status_file.write_text(
            self._status.model_dump_json(indent=2),
            encoding="utf-8",
        )

    def start_stage(self, stage: PipelineStage, message: str = "") -> None:
        """Mark a stage as started."""
        self._status.current_stage = stage
        self._status.status = StatusEnum.RUNNING
        self._status.progress = 0.0
        self._status.error = None
        self._status.updated_at = datetime.now(timezone.utc)
        self._save()

        event = SSEEvent(
            project_id=self.project_id,
            stage=stage,
            status=StatusEnum.RUNNING,
            progress=0.0,
            message=message or f"Starting {stage.value}",
        )
        self._events.append(event)

    def update_progress(
        self,
        stage: PipelineStage,
        progress: float,
        chapter_id: str | None = None,
        message: str = "",
    ) -> None:
        """Update progress within a stage."""
        self._status.progress = min(1.0, max(0.0, progress))
        self._status.updated_at = datetime.now(timezone.utc)
        self._save()

        event = SSEEvent(
            project_id=self.project_id,
            stage=stage,
            status=StatusEnum.RUNNING,
            chapter_id=chapter_id,
            progress=self._status.progress,
            message=message,
        )
        self._events.append(event)

    def complete_stage(self, stage: PipelineStage, message: str = "") -> None:
        """Mark a stage as completed."""
        self._status.progress = 1.0
        self._status.status = StatusEnum.SUCCEEDED
        self._status.updated_at = datetime.now(timezone.utc)
        self._save()

        event = SSEEvent(
            project_id=self.project_id,
            stage=stage,
            status=StatusEnum.SUCCEEDED,
            progress=1.0,
            message=message or f"{stage.value} completed",
        )
        self._events.append(event)

    def fail_stage(self, stage: PipelineStage, error: str) -> None:
        """Mark a stage as failed."""
        self._status.status = StatusEnum.FAILED
        self._status.error = error
        self._status.updated_at = datetime.now(timezone.utc)
        self._save()

        event = SSEEvent(
            project_id=self.project_id,
            stage=stage,
            status=StatusEnum.FAILED,
            progress=self._status.progress,
            message=error,
        )
        self._events.append(event)

    def reset(self) -> None:
        """Reset status to idle."""
        self._status = PipelineStatus(project_id=self.project_id)
        self._save()

    async def event_stream(self) -> AsyncIterator[SSEEvent]:
        """Yield SSE events as they are produced."""
        idx = 0
        while True:
            if idx < len(self._events):
                yield self._events[idx]
                idx += 1
            else:
                # Check if pipeline is done
                if self._status.status in (
                    StatusEnum.SUCCEEDED,
                    StatusEnum.FAILED,
                    StatusEnum.CANCELLED,
                    StatusEnum.IDLE,
                ):
                    break
                await asyncio.sleep(0.2)


def get_status(project_id: str) -> PipelineStatus:
    """Read current pipeline status from status.json."""
    status_file = get_project_dir(project_id) / "status.json"
    if not status_file.exists():
        return PipelineStatus(project_id=project_id)
    data = json.loads(status_file.read_text(encoding="utf-8"))
    return PipelineStatus.model_validate(data)
