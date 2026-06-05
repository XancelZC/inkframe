"""Tests for Issue #9: YAML export."""

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


class TestExport:
    def test_export_yaml(self):
        pid = _full_pipeline("Export Test", "Chapter 1\n\nTom met Jane.")
        resp = client.get(f"/api/projects/{pid}/export")
        assert resp.status_code == 200
        assert "yaml" in resp.headers.get("content-type", "")
        assert "attachment" in resp.headers.get("content-disposition", "")

    def test_export_content_is_valid_yaml(self):
        pid = _full_pipeline("Export YAML", "Chapter 1\n\nTom said hello.")
        resp = client.get(f"/api/projects/{pid}/export")
        import yaml
        data = yaml.safe_load(resp.content)
        assert "metadata" in data
        assert "characters" in data
        assert "acts" in data

    def test_export_not_generated(self):
        resp = client.post("/api/projects", data={"title": "No Export", "text": "text"})
        pid = resp.json()["id"]
        resp = client.get(f"/api/projects/{pid}/export")
        assert resp.status_code == 404

    def test_export_not_found(self):
        resp = client.get("/api/projects/prj_nonexistent_9999999999/export")
        assert resp.status_code == 404
