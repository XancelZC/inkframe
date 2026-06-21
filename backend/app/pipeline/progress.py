"""Pipeline progress tracking and SSE events.

Writes status.json during pipeline runs and provides
an async event stream for the frontend.

跨线程通信：process_project 在 FastAPI 线程池里运行（同步），
event_stream 在事件循环协程里运行。用 asyncio.Queue +
loop.call_soon_threadsafe 实现跨线程安全的事件传递。
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import AsyncIterator

from app.models.status import PipelineStatus, PipelineStage, StatusEnum
from app.models.events import SSEEvent
from app.storage import get_project_dir

_SENTINEL = object()  # 标记队列结束


class ProgressTracker:
    """Tracks pipeline progress and emits SSE events.

    线程安全：所有公开方法从线程池同步调用，
    通过 loop.call_soon_threadsafe 把事件放入 asyncio.Queue。
    """

    def __init__(self, project_id: str) -> None:
        self.project_id = project_id
        self._status = PipelineStatus(project_id=project_id)
        self._queue: asyncio.Queue = asyncio.Queue()
        # 记录创建时的事件循环（应在 async 上下文中创建）
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            self._loop = None
        self._save()

    def _save(self) -> None:
        status_file = get_project_dir(self.project_id) / "status.json"
        status_file.write_text(
            self._status.model_dump_json(indent=2),
            encoding="utf-8",
        )

    def _put(self, item) -> None:
        """线程安全地把 item 放入队列。"""
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._queue.put_nowait, item)
        else:
            # 兜底：直接 put（测试环境同步场景）
            try:
                self._queue.put_nowait(item)
            except Exception:
                pass

    def start_stage(self, stage: PipelineStage, message: str = "") -> None:
        self._status.current_stage = stage
        self._status.status = StatusEnum.RUNNING
        self._status.progress = 0.0
        self._status.error = None
        self._status.updated_at = datetime.now(timezone.utc)
        self._save()
        self._put(SSEEvent(
            project_id=self.project_id,
            stage=stage,
            status=StatusEnum.RUNNING,
            progress=0.0,
            message=message or f"Starting {stage.value}",
        ))

    def update_progress(
        self,
        stage: PipelineStage,
        progress: float,
        chapter_id: str | None = None,
        message: str = "",
    ) -> None:
        self._status.progress = min(1.0, max(0.0, progress))
        self._status.updated_at = datetime.now(timezone.utc)
        self._save()
        self._put(SSEEvent(
            project_id=self.project_id,
            stage=stage,
            status=StatusEnum.RUNNING,
            chapter_id=chapter_id,
            progress=self._status.progress,
            message=message,
        ))

    def complete_stage(self, stage: PipelineStage, message: str = "", final: bool = True) -> None:
        """Mark a stage as completed. Set final=False when more stages will follow."""
        self._status.progress = 1.0
        if final:
            self._status.status = StatusEnum.SUCCEEDED
        self._status.updated_at = datetime.now(timezone.utc)
        self._save()
        event_status = StatusEnum.SUCCEEDED if final else StatusEnum.STAGE_COMPLETED
        self._put(SSEEvent(
            project_id=self.project_id,
            stage=stage,
            status=event_status,
            progress=1.0,
            message=message or f"{stage.value} completed",
        ))

    def finish(self, message: str = "") -> None:
        """Mark the entire pipeline run as finished and close the stream."""
        self._status.status = StatusEnum.SUCCEEDED
        self._status.updated_at = datetime.now(timezone.utc)
        self._save()
        self._put(SSEEvent(
            project_id=self.project_id,
            stage=self._status.current_stage or PipelineStage.VALIDATION,
            status=StatusEnum.SUCCEEDED,
            progress=1.0,
            message=message or "全部完成",
        ))
        self._put(_SENTINEL)
        _trackers.pop(self.project_id, None)

    def fail_stage(self, stage: PipelineStage, error: str) -> None:
        self._status.status = StatusEnum.FAILED
        self._status.error = error
        self._status.updated_at = datetime.now(timezone.utc)
        self._save()
        self._put(SSEEvent(
            project_id=self.project_id,
            stage=stage,
            status=StatusEnum.FAILED,
            progress=self._status.progress,
            message=error,
        ))
        self._put(_SENTINEL)
        _trackers.pop(self.project_id, None)

    def reset(self) -> None:
        self._status = PipelineStatus(project_id=self.project_id)
        self._save()

    async def event_stream(self) -> AsyncIterator[SSEEvent]:
        """从队列读事件，直到收到 sentinel。"""
        while True:
            item = await self._queue.get()
            if item is _SENTINEL:
                break
            yield item


def get_status(project_id: str) -> PipelineStatus:
    """Read current pipeline status from status.json."""
    status_file = get_project_dir(project_id) / "status.json"
    if not status_file.exists():
        return PipelineStatus(project_id=project_id)
    data = json.loads(status_file.read_text(encoding="utf-8"))
    return PipelineStatus.model_validate(data)


# 进程级 tracker 注册表，供 process 和 events 端点共享同一实例
_trackers: dict[str, ProgressTracker] = {}


def get_or_create_tracker(project_id: str) -> ProgressTracker:
    """新建该 project 的 ProgressTracker 并注册，供 SSE 端点共享。"""
    tracker = ProgressTracker(project_id)
    _trackers[project_id] = tracker
    return tracker


def get_tracker(project_id: str) -> ProgressTracker | None:
    """获取已有的 tracker（供 SSE 端点使用）。"""
    return _trackers.get(project_id)
