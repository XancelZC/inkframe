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

    def test_import_novel_creates_chapters_from_multiple_files(self):
        resp = client.post(
            "/api/novels/import",
            files=[
                ("files", ("chapter-10.txt", b"ten", "text/plain")),
                ("files", ("chapter-2.txt", b"two", "text/plain")),
                ("relative_paths", (None, "卷一/chapter-10.txt")),
                ("relative_paths", (None, "卷一/chapter-2.txt")),
            ],
            data={"title": "批量导入小说", "language": "zh"},
        )

        assert resp.status_code == 201
        data = resp.json()
        assert data["created_count"] == 2
        assert data["failed_count"] == 0
        assert [c["title"] for c in data["created_chapters"]] == ["chapter-2", "chapter-10"]

        novel_id = data["novel"]["id"]
        detail = client.get(f"/api/novels/{novel_id}").json()
        assert detail["chapter_count"] == 2
        assert [c["title"] for c in detail["chapters"]] == ["chapter-2", "chapter-10"]

    def test_import_chapters_keeps_successes_when_some_files_fail(self):
        novel_resp = client.post("/api/novels", params={"title": "部分失败"})
        novel_id = novel_resp.json()["id"]

        resp = client.post(
            f"/api/novels/{novel_id}/chapters/import",
            files=[
                ("files", ("valid.txt", b"valid content", "text/plain")),
                ("files", ("empty.txt", b"   ", "text/plain")),
                ("files", (".DS_Store", b"ignored", "application/octet-stream")),
                ("relative_paths", (None, "valid.txt")),
                ("relative_paths", (None, "empty.txt")),
                ("relative_paths", (None, ".DS_Store")),
            ],
        )

        assert resp.status_code == 201
        data = resp.json()
        assert data["created_count"] == 1
        assert data["failed_count"] == 1
        assert data["ignored_count"] == 1
        assert data["created_chapters"][0]["title"] == "valid"
        assert data["failed_files"][0]["path"] == "empty.txt"

        detail = client.get(f"/api/novels/{novel_id}").json()
        assert detail["chapter_count"] == 1

    def test_import_chapters_decodes_gb18030_text(self):
        novel_resp = client.post("/api/novels", params={"title": "编码测试"})
        novel_id = novel_resp.json()["id"]
        gb_text = "第一章 中文内容".encode("gb18030")

        resp = client.post(
            f"/api/novels/{novel_id}/chapters/import",
            files=[
                ("files", ("gbk.txt", gb_text, "text/plain")),
                ("relative_paths", (None, "gbk.txt")),
            ],
        )

        assert resp.status_code == 201
        data = resp.json()
        assert data["created_count"] == 1
        chapter_id = data["created_chapters"][0]["id"]
        project = client.get(f"/api/projects/{chapter_id}").json()
        assert project["raw_text"] == "第一章 中文内容"

    def test_import_chapters_suffixes_duplicate_titles(self):
        novel_resp = client.post("/api/novels", params={"title": "重名测试"})
        novel_id = novel_resp.json()["id"]
        client.post(f"/api/novels/{novel_id}/chapters", data={"title": "第01章", "text": "旧内容"})

        resp = client.post(
            f"/api/novels/{novel_id}/chapters/import",
            files=[
                ("files", ("a.txt", b"first", "text/plain")),
                ("files", ("b.txt", b"second", "text/plain")),
                ("relative_paths", (None, "卷一/第01章.txt")),
                ("relative_paths", (None, "卷二/第01章.txt")),
            ],
        )

        assert resp.status_code == 201
        data = resp.json()
        assert [c["title"] for c in data["created_chapters"]] == ["第01章 (2)", "第01章 (3)"]
