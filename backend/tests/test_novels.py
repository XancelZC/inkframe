"""Tests for novel (folder) API."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestNovelAPI:
    def test_list_novels_empty(self):
        resp = client.get("/api/novels")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_create_novel(self):
        resp = client.post("/api/novels", params={"title": "测试小说", "language": "zh"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "测试小说"
        assert data["language"] == "zh"
        assert data["id"].startswith("nvl_")

    def test_get_novel_with_chapters(self):
        # 创建小说
        novel_resp = client.post("/api/novels", params={"title": "带章节小说", "language": "zh"})
        novel_id = novel_resp.json()["id"]

        # 添加章节（使用 form data）
        client.post(f"/api/novels/{novel_id}/chapters", data={"title": "第一章", "text": "这是第一章内容"})
        client.post(f"/api/novels/{novel_id}/chapters", data={"title": "第二章", "text": "这是第二章内容"})

        # 获取小说详情
        resp = client.get(f"/api/novels/{novel_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "带章节小说"
        assert data["chapter_count"] == 2
        assert len(data["chapters"]) == 2
        assert data["chapters"][0]["title"] == "第一章"

    def test_delete_novel(self):
        novel_resp = client.post("/api/novels", params={"title": "待删除小说"})
        novel_id = novel_resp.json()["id"]

        resp = client.delete(f"/api/novels/{novel_id}")
        assert resp.status_code == 200

        # 确认已删除
        resp = client.get(f"/api/novels/{novel_id}")
        assert resp.status_code == 404

    def test_delete_novel_cascades_chapters(self):
        novel_resp = client.post("/api/novels", params={"title": "级联删除"})
        novel_id = novel_resp.json()["id"]

        chapter_resp = client.post(f"/api/novels/{novel_id}/chapters", data={"title": "第一章"})
        chapter_id = chapter_resp.json()["id"]

        # 删除小说
        client.delete(f"/api/novels/{novel_id}")

        # 章节也应该被删除
        resp = client.get(f"/api/projects/{chapter_id}")
        assert resp.status_code == 404

    def test_create_chapter_in_novel(self):
        novel_resp = client.post("/api/novels", params={"title": "章节测试"})
        novel_id = novel_resp.json()["id"]

        resp = client.post(f"/api/novels/{novel_id}/chapters", data={"title": "第一节", "text": "内容"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "第一节"
        assert data["novel_id"] == novel_id

    def test_create_chapter_rejects_empty_title(self):
        novel_resp = client.post("/api/novels", params={"title": "空标题测试"})
        novel_id = novel_resp.json()["id"]

        resp = client.post(f"/api/novels/{novel_id}/chapters", data={"title": ""})
        # FastAPI 对空 Form 字段返回 422
        assert resp.status_code in (400, 422)

    def test_create_chapter_rejects_missing_novel(self):
        resp = client.post("/api/novels/nvl_nonexistent/chapters", data={"title": "不存在"})
        assert resp.status_code == 404
