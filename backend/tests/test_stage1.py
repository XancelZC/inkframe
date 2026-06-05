"""Tests for Issue #5: Character extraction with mock provider."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _create_and_preprocess(title: str, text: str) -> str:
    """Helper: create a project and run Stage 0."""
    resp = client.post("/api/projects", data={"title": title, "text": text})
    project_id = resp.json()["id"]
    client.post(f"/api/projects/{project_id}/process")
    return project_id


class TestStage1API:
    def test_extract_characters(self):
        project_id = _create_and_preprocess(
            "Char Test",
            "Chapter 1\n\nXiangzi pulled his rickshaw down the street.\n\nChapter 2\n\nHuniu sat in the teahouse.",
        )

        resp = client.post(f"/api/projects/{project_id}/process?from_stage=character_extraction")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "succeeded"
        assert data["stage"] == "character_extraction"
        assert data["characters"] >= 1

    def test_get_characters(self):
        project_id = _create_and_preprocess("Get Char", "Chapter 1\n\nTom met Jane at the park.")
        client.post(f"/api/projects/{project_id}/process?from_stage=character_extraction")

        resp = client.get(f"/api/projects/{project_id}/characters")
        assert resp.status_code == 200
        data = resp.json()
        assert "characters" in data
        assert len(data["characters"]) >= 1
        # Each character should have required fields
        for char in data["characters"]:
            assert "id" in char
            assert "name" in char
            assert char["id"].startswith("char_")

    def test_characters_not_extracted_yet(self):
        project_id = _create_and_preprocess("No Char", "Some text")
        resp = client.get(f"/api/projects/{project_id}/characters")
        assert resp.status_code == 404

    def test_update_characters(self):
        project_id = _create_and_preprocess("Edit Char", "Chapter 1\n\nTom met Jane.")
        client.post(f"/api/projects/{project_id}/process?from_stage=character_extraction")

        # Get current characters
        current = client.get(f"/api/projects/{project_id}/characters").json()

        # Modify a character name
        if current["characters"]:
            current["characters"][0]["name"] = "Modified Name"
            current["characters"][0]["description"] = "Updated description"

            resp = client.put(f"/api/projects/{project_id}/characters", json=current)
            assert resp.status_code == 200
            assert resp.json()["status"] == "saved"

            # Verify the change persisted
            updated = client.get(f"/api/projects/{project_id}/characters").json()
            assert updated["characters"][0]["name"] == "Modified Name"

    def test_update_characters_rejects_invalid(self):
        project_id = _create_and_preprocess("Invalid Char", "Some text")
        # "characters" must be a list, not a string
        resp = client.put(
            f"/api/projects/{project_id}/characters", json={"characters": "not_a_list"}
        )
        assert resp.status_code == 400

    def test_stage1_requires_stage0(self):
        resp = client.post("/api/projects", data={"title": "No Stage0", "text": "text"})
        project_id = resp.json()["id"]

        resp = client.post(f"/api/projects/{project_id}/process?from_stage=character_extraction")
        assert resp.status_code == 400
