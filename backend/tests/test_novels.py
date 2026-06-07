"""Tests for novel (folder) API."""

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
        assert data["pinned"] is False
        assert data["id"].startswith("nvl_")

    def test_get_novel_with_chapters(self):
        novel_resp = client.post("/api/novels", params={"title": "带章节小说", "language": "zh"})
        novel_id = novel_resp.json()["id"]

        client.post(
            f"/api/novels/{novel_id}/chapters",
            data={"title": "第一章", "text": "这是第一章内容"},
        )
        client.post(
            f"/api/novels/{novel_id}/chapters",
            data={"title": "第二章", "text": "这是第二章内容"},
        )

        resp = client.get(f"/api/novels/{novel_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "带章节小说"
        assert data["pinned"] is False
        assert data["chapter_count"] == 2
        assert len(data["chapters"]) == 2
        assert data["chapters"][0]["title"] == "第一章"

    def test_delete_novel(self):
        novel_resp = client.post("/api/novels", params={"title": "待删除小说"})
        novel_id = novel_resp.json()["id"]

        resp = client.delete(f"/api/novels/{novel_id}")
        assert resp.status_code == 200

        resp = client.get(f"/api/novels/{novel_id}")
        assert resp.status_code == 404

    def test_pin_and_unpin_novel(self):
        novel_resp = client.post("/api/novels", params={"title": "置顶测试"})
        novel_id = novel_resp.json()["id"]

        pin_resp = client.put(f"/api/novels/{novel_id}/pin", params={"pinned": True})
        assert pin_resp.status_code == 200
        assert pin_resp.json()["pinned"] is True

        list_resp = client.get("/api/novels")
        assert list_resp.status_code == 200
        pinned_novel = next(n for n in list_resp.json() if n["id"] == novel_id)
        assert pinned_novel["pinned"] is True

        unpin_resp = client.put(f"/api/novels/{novel_id}/pin", params={"pinned": False})
        assert unpin_resp.status_code == 200
        assert unpin_resp.json()["pinned"] is False

    def test_pin_missing_novel(self):
        resp = client.put("/api/novels/nvl_nonexistent/pin", params={"pinned": True})
        assert resp.status_code == 404

    def test_delete_novel_cascades_chapters(self):
        novel_resp = client.post("/api/novels", params={"title": "级联删除"})
        novel_id = novel_resp.json()["id"]

        chapter_resp = client.post(f"/api/novels/{novel_id}/chapters", data={"title": "第一章"})
        chapter_id = chapter_resp.json()["id"]

        client.delete(f"/api/novels/{novel_id}")

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
        assert resp.status_code in (400, 422)

    def test_create_chapter_rejects_missing_novel(self):
        resp = client.post("/api/novels/nvl_nonexistent/chapters", data={"title": "不存在"})
        assert resp.status_code == 404
