"""Tests for Issue #3: Create project from pasted or uploaded text."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.storage import detect_language, get_project_dir

client = TestClient(app)


class TestCreateProjectFromText:
    def test_create_from_pasted_text(self):
        resp = client.post(
            "/api/projects",
            data={"title": "Paste Test", "text": "这是祥子的故事。他拉着车走在北平的街上。"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Paste Test"
        assert data["source_language"] == "zh"
        assert data["id"].startswith("prj_")

    def test_create_from_file_upload(self):
        resp = client.post(
            "/api/projects",
            data={"title": "File Test"},
            files={"file": ("novel.txt", "This is a test novel.\nChapter one.", "text/plain")},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "File Test"
        assert data["source_language"] == "en"

    def test_create_rejects_empty_text(self):
        resp = client.post("/api/projects", data={"title": "Empty", "text": ""})
        assert resp.status_code == 400

    def test_create_rejects_no_content(self):
        resp = client.post("/api/projects", data={"title": "No Content"})
        assert resp.status_code == 400

    def test_manual_language_override(self):
        resp = client.post(
            "/api/projects",
            data={"title": "Lang Override", "source_language": "en", "text": "English text"},
        )
        assert resp.status_code == 201
        assert resp.json()["source_language"] == "en"

    def test_raw_text_persisted(self):
        test_text = "祥子拉着车穿过清晨的街口。"
        create_resp = client.post(
            "/api/projects", data={"title": "Persist Test", "text": test_text}
        )
        project_id = create_resp.json()["id"]

        detail_resp = client.get(f"/api/projects/{project_id}")
        assert detail_resp.status_code == 200
        assert detail_resp.json()["raw_text"] == test_text


class TestUpdateProjectSource:
    def test_update_source_text_invalidates_generated_outputs(self):
        create_resp = client.post(
            "/api/projects",
            data={"title": "Editable Source", "text": "旧原文。"},
        )
        project_id = create_resp.json()["id"]
        project_dir = get_project_dir(project_id)
        generated_files = [
            "02_preprocessed.json",
            "03_characters.json",
            "04_scenes.json",
            "05_validated.json",
            "06_screenplay.generated.yaml",
            "07_screenplay.edited.yaml",
            "validation_log.json",
        ]
        for filename in generated_files:
            (project_dir / filename).write_text("stale", encoding="utf-8")

        updated_text = "新原文第一行。\n\n新原文第二行。"
        resp = client.put(
            f"/api/projects/{project_id}/source",
            json={"raw_text": updated_text},
        )

        assert resp.status_code == 200
        assert resp.json()["raw_text"] == updated_text
        assert (project_dir / "01_raw.txt").read_text(encoding="utf-8") == updated_text
        assert all(not (project_dir / filename).exists() for filename in generated_files)

    def test_update_source_rejects_blank_text(self):
        create_resp = client.post(
            "/api/projects",
            data={"title": "Reject Blank Source", "text": "原文。"},
        )
        project_id = create_resp.json()["id"]

        resp = client.put(
            f"/api/projects/{project_id}/source",
            json={"raw_text": "   \n\t  "},
        )

        assert resp.status_code == 400


class TestLanguageDetection:
    def test_detect_chinese(self):
        assert detect_language("这是中文小说。祥子拉着车。") == "zh"

    def test_detect_english(self):
        assert detect_language("This is an English novel. John walked down the street.") == "en"

    def test_detect_empty_defaults_zh(self):
        assert detect_language("") == "zh"
