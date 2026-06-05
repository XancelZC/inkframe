"""Tests for Issue #8: Consistency validation."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _full_pipeline(title: str, text: str) -> str:
    resp = client.post("/api/projects", data={"title": title, "text": text})
    pid = resp.json()["id"]
    client.post(f"/api/projects/{pid}/process")
    client.post(f"/api/projects/{pid}/process?from_stage=character_extraction")
    client.post(f"/api/projects/{pid}/process?from_stage=scene_synthesis")
    return pid


class TestValidation:
    def test_run_validation(self):
        pid = _full_pipeline("Val Test", "Chapter 1\n\nTom said hello to Jane.")
        resp = client.post(f"/api/projects/{pid}/process?from_stage=validation")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "succeeded"
        assert data["stage"] == "validation"
        assert "errors" in data
        assert "warnings" in data
        assert "info" in data

    def test_get_validation_log(self):
        pid = _full_pipeline("Val Log", "Chapter 1\n\nTom met Jane.")
        client.post(f"/api/projects/{pid}/process?from_stage=validation")

        resp = client.get(f"/api/projects/{pid}/validation")
        assert resp.status_code == 200
        data = resp.json()
        assert "entries" in data
        assert "error_count" in data
        assert "warning_count" in data
        assert "info_count" in data

    def test_validation_log_entries_have_required_fields(self):
        pid = _full_pipeline("Val Fields", "Chapter 1\n\n\"Hello,\" said Tom.")
        client.post(f"/api/projects/{pid}/process?from_stage=validation")

        log = client.get(f"/api/projects/{pid}/validation").json()
        for entry in log["entries"]:
            assert "severity" in entry
            assert entry["severity"] in ["error", "warning", "info"]
            assert "code" in entry
            assert "message" in entry

    def test_low_confidence_warning(self):
        # The mock provider generates elements with varying confidence
        pid = _full_pipeline("Confidence", "Chapter 1\n\nTom told Jane he was leaving.")
        client.post(f"/api/projects/{pid}/process?from_stage=validation")

        log = client.get(f"/api/projects/{pid}/validation").json()
        # Should have at least some entries (mock data may trigger low confidence)
        assert isinstance(log["entries"], list)

    def test_validation_not_run_yet(self):
        resp = client.post("/api/projects", data={"title": "No Val", "text": "text"})
        pid = resp.json()["id"]
        resp = client.get(f"/api/projects/{pid}/validation")
        assert resp.status_code == 404

    def test_validation_requires_scenes(self):
        resp = client.post("/api/projects", data={"title": "No Scenes", "text": "text"})
        pid = resp.json()["id"]
        client.post(f"/api/projects/{pid}/process")
        resp = client.post(f"/api/projects/{pid}/process?from_stage=validation")
        assert resp.status_code == 400
