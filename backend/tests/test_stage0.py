"""Tests for Issue #4: Stage 0 preprocessing."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.pipeline.stage0 import run_stage0, _split_into_chapters, _split_into_paragraphs

client = TestClient(app)


class TestChapterSplitting:
    def test_single_chapter_no_markers(self):
        chapters = _split_into_chapters("This is a single block of text without markers.")
        assert len(chapters) == 1
        assert chapters[0][0] is None

    def test_split_by_chapter_marker(self):
        text = "Chapter 1\n\nTom walked down the street.\n\nChapter 2\n\nJane sat in the park."
        chapters = _split_into_chapters(text)
        assert len(chapters) == 2
        assert "Chapter 1" in chapters[0][0]
        assert "Chapter 2" in chapters[1][0]

    def test_split_by_chinese_marker(self):
        text = "第一章\n祥子拉着车走在街上。\n第二章\n祥子回到了家。"
        chapters = _split_into_chapters(text)
        assert len(chapters) == 2

    def test_split_three_chapters(self):
        text = "Chapter 1\nText one.\nChapter 2\nText two.\nChapter 3\nText three."
        chapters = _split_into_chapters(text)
        assert len(chapters) == 3


class TestParagraphSplitting:
    def test_single_paragraph(self):
        paras = _split_into_paragraphs("Single paragraph text.")
        assert len(paras) == 1
        assert paras[0][0] == "Single paragraph text."

    def test_multiple_paragraphs(self):
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        paras = _split_into_paragraphs(text)
        assert len(paras) == 3
        assert paras[0][0] == "First paragraph."
        assert paras[1][0] == "Second paragraph."
        assert paras[2][0] == "Third paragraph."

    def test_offsets_are_correct(self):
        text = "First paragraph.\n\nSecond paragraph."
        paras = _split_into_paragraphs(text)
        for para_text, start, end in paras:
            assert text[start:end].strip() == para_text


class TestStage0Integration:
    def test_run_stage0_from_api(self):
        # Create project with multi-chapter text
        text = "Chapter 1\nTom walked down the street.\n\nChapter 2\nJane sat in the park."
        create_resp = client.post(
            "/api/projects",
            data={"title": "Stage0 Test", "text": text},
        )
        assert create_resp.status_code == 201
        project_id = create_resp.json()["id"]

        # Run preprocessing
        process_resp = client.post(f"/api/projects/{project_id}/process")
        assert process_resp.status_code == 200
        data = process_resp.json()
        assert data["status"] == "succeeded"
        assert data["stage"] == "preprocessing"
        assert data["chapters"] >= 1
        assert data["paragraphs"] >= 1

    def test_get_stage_result(self):
        create_resp = client.post(
            "/api/projects",
            data={"title": "Stage Result Test", "text": "Chapter 1\n\nPara one.\n\nPara two."},
        )
        project_id = create_resp.json()["id"]

        client.post(f"/api/projects/{project_id}/process")

        result_resp = client.get(f"/api/projects/{project_id}/stages/preprocessing")
        assert result_resp.status_code == 200
        data = result_resp.json()
        assert "chapters" in data
        assert "detected_language" in data
        assert len(data["chapters"]) >= 1

    def test_stage_result_not_found(self):
        create_resp = client.post(
            "/api/projects", data={"title": "No Stage", "text": "text"}
        )
        project_id = create_resp.json()["id"]

        resp = client.get(f"/api/projects/{project_id}/stages/preprocessing")
        assert resp.status_code == 404

    def test_process_rejects_missing_project(self):
        resp = client.post("/api/projects/prj_nonexistent_9999999999/process")
        assert resp.status_code == 404

    def test_stage_ids_are_stable(self):
        create_resp = client.post(
            "/api/projects", data={"title": "ID Test", "text": "Chapter 1\n\nPara one."}
        )
        project_id = create_resp.json()["id"]
        client.post(f"/api/projects/{project_id}/process")

        result = client.get(f"/api/projects/{project_id}/stages/preprocessing").json()
        ch_id = result["chapters"][0]["id"]
        para_id = result["chapters"][0]["paragraphs"][0]["id"]
        assert ch_id.startswith("ch_")
        assert para_id.startswith("p_")
