"""Tests for Issue #7: Progress status and SSE events."""

import json
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.status import PipelineStatus, PipelineStage, StatusEnum
from app.pipeline.progress import ProgressTracker, get_status

client = TestClient(app)


def _create_project(title: str = "Progress Test", text: str = "Some text") -> str:
    resp = client.post("/api/projects", data={"title": title, "text": text})
    return resp.json()["id"]


class TestProgressTracker:
    def test_initial_status_is_idle(self):
        pid = _create_project("Init Status")
        status = get_status(pid)
        assert status.status == StatusEnum.IDLE
        assert status.progress == 0.0

    def test_start_stage_updates_status(self):
        pid = _create_project("Start Stage")
        tracker = ProgressTracker(pid)
        tracker.start_stage(PipelineStage.PREPROCESSING, "Starting preprocessing")

        status = get_status(pid)
        assert status.status == StatusEnum.RUNNING
        assert status.current_stage == PipelineStage.PREPROCESSING
        assert status.progress == 0.0

    def test_update_progress(self):
        pid = _create_project("Update Progress")
        tracker = ProgressTracker(pid)
        tracker.start_stage(PipelineStage.PREPROCESSING)
        tracker.update_progress(PipelineStage.PREPROCESSING, 0.5, message="Half done")

        status = get_status(pid)
        assert status.progress == 0.5

    def test_progress_capped_at_1(self):
        pid = _create_project("Cap Progress")
        tracker = ProgressTracker(pid)
        tracker.start_stage(PipelineStage.PREPROCESSING)
        tracker.update_progress(PipelineStage.PREPROCESSING, 1.5)

        status = get_status(pid)
        assert status.progress == 1.0

    def test_complete_stage(self):
        pid = _create_project("Complete Stage")
        tracker = ProgressTracker(pid)
        tracker.start_stage(PipelineStage.PREPROCESSING)
        tracker.complete_stage(PipelineStage.PREPROCESSING, "Done")

        status = get_status(pid)
        assert status.status == StatusEnum.SUCCEEDED
        assert status.progress == 1.0

    def test_fail_stage(self):
        pid = _create_project("Fail Stage")
        tracker = ProgressTracker(pid)
        tracker.start_stage(PipelineStage.PREPROCESSING)
        tracker.fail_stage(PipelineStage.PREPROCESSING, "Something broke")

        status = get_status(pid)
        assert status.status == StatusEnum.FAILED
        assert status.error == "Something broke"

    def test_events_are_recorded(self):
        pid = _create_project("Events")
        tracker = ProgressTracker(pid)
        tracker.start_stage(PipelineStage.PREPROCESSING)
        tracker.update_progress(PipelineStage.PREPROCESSING, 0.5)
        tracker.complete_stage(PipelineStage.PREPROCESSING)

        assert tracker._queue.qsize() == 3


class TestStatusAPI:
    def test_get_status(self):
        pid = _create_project("Status API")
        resp = client.get(f"/api/projects/{pid}/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "idle"
        assert data["project_id"] == pid

    def test_status_not_found(self):
        resp = client.get("/api/projects/prj_nonexistent_9999999999/status")
        assert resp.status_code == 404

    def test_status_updates_after_process(self):
        pid = _create_project("Status After Process")
        client.post(f"/api/projects/{pid}/process")
        resp = client.get(f"/api/projects/{pid}/status")
        assert resp.status_code == 200
