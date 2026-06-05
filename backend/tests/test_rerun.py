"""Tests for Issue #11: Re-run pipeline from specific stage."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _create_project(title: str = "Rerun Test", text: str = "Chapter 1\n\nTom met Jane.") -> str:
    resp = client.post("/api/projects", data={"title": title, "text": text})
    return resp.json()["id"]


class TestRerunStage:
    def test_rerun_from_stage0(self):
        pid = _create_project("Rerun 0")
        resp = client.post(f"/api/projects/{pid}/process?from_stage=preprocessing")
        assert resp.status_code == 200

    def test_rerun_from_stage1(self):
        pid = _create_project("Rerun 1")
        client.post(f"/api/projects/{pid}/process")
        resp = client.post(f"/api/projects/{pid}/process?from_stage=character_extraction")
        assert resp.status_code == 200

    def test_rerun_from_stage2(self):
        pid = _create_project("Rerun 2")
        client.post(f"/api/projects/{pid}/process")
        client.post(f"/api/projects/{pid}/process?from_stage=character_extraction")
        resp = client.post(f"/api/projects/{pid}/process?from_stage=scene_synthesis")
        assert resp.status_code == 200

    def test_rerun_from_stage3(self):
        pid = _create_project("Rerun 3")
        client.post(f"/api/projects/{pid}/process")
        client.post(f"/api/projects/{pid}/process?from_stage=character_extraction")
        client.post(f"/api/projects/{pid}/process?from_stage=scene_synthesis")
        resp = client.post(f"/api/projects/{pid}/process?from_stage=validation")
        assert resp.status_code == 200

    def test_rerun_stage1_without_stage0(self):
        pid = _create_project("No Prereq")
        resp = client.post(f"/api/projects/{pid}/process?from_stage=character_extraction")
        assert resp.status_code == 400
        assert "prerequisite" in resp.json()["detail"].lower()

    def test_rerun_stage2_without_stage1(self):
        pid = _create_project("No S1")
        client.post(f"/api/projects/{pid}/process")
        resp = client.post(f"/api/projects/{pid}/process?from_stage=scene_synthesis")
        assert resp.status_code == 400

    def test_rerun_stage3_without_stage2(self):
        pid = _create_project("No S2")
        client.post(f"/api/projects/{pid}/process")
        client.post(f"/api/projects/{pid}/process?from_stage=character_extraction")
        resp = client.post(f"/api/projects/{pid}/process?from_stage=validation")
        assert resp.status_code == 400

    def test_rerun_unknown_stage(self):
        pid = _create_project("Unknown")
        resp = client.post(f"/api/projects/{pid}/process?from_stage=nonexistent")
        assert resp.status_code == 400

    def test_rerun_preserves_downstream_data(self):
        pid = _create_project("Preserve")
        # Run full pipeline
        client.post(f"/api/projects/{pid}/process")
        client.post(f"/api/projects/{pid}/process?from_stage=character_extraction")
        client.post(f"/api/projects/{pid}/process?from_stage=scene_synthesis")

        # Re-run stage 0
        client.post(f"/api/projects/{pid}/process?from_stage=preprocessing")

        # Stage 0 result should still exist
        resp = client.get(f"/api/projects/{pid}/stages/preprocessing")
        assert resp.status_code == 200
