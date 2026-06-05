"""Tests for Issue #2: Bootstrap monorepo with mock provider and project list."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.llm.mock import MockProvider


client = TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_ok(self):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestProjectListAPI:
    def test_list_projects_empty(self):
        resp = client.get("/api/projects")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_create_project(self):
        resp = client.post(
            "/api/projects",
            data={"title": "Test Novel", "source_language": "zh", "text": "Some novel text"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Test Novel"
        assert data["id"].startswith("prj_")

    def test_list_projects_after_create(self):
        resp = client.get("/api/projects")
        assert resp.status_code == 200
        projects = resp.json()
        assert len(projects) >= 1
        assert any(p["title"] == "Test Novel" for p in projects)

    def test_get_project_detail(self):
        # Create a project first
        create_resp = client.post(
            "/api/projects", data={"title": "Detail Test", "text": "Some text"}
        )
        project_id = create_resp.json()["id"]

        resp = client.get(f"/api/projects/{project_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == project_id
        assert data["title"] == "Detail Test"

    def test_get_project_not_found(self):
        resp = client.get("/api/projects/prj_nonexistent_9999999999")
        assert resp.status_code == 404


class TestModelsAPI:
    def test_get_config(self):
        resp = client.get("/api/models/config")
        assert resp.status_code == 200
        data = resp.json()
        assert "active_provider_id" in data
        assert "providers" in data
        assert len(data["providers"]) >= 1
        mock = next(p for p in data["providers"] if p["id"] == "mock")
        assert mock["type"] == "mock"


class TestMockProvider:
    def test_provider_id(self):
        p = MockProvider()
        assert p.provider_id == "mock"

    def test_list_models(self):
        p = MockProvider()
        assert "mock-screenplay" in p.list_models()

    def test_generate_json_returns_dict(self):
        p = MockProvider()
        result = p.generate_json("test prompt", {"type": "object", "properties": {"name": {"type": "string"}}})
        assert isinstance(result, dict)
        assert "name" in result

    @pytest.mark.asyncio
    async def test_stream_json_yields_result(self):
        p = MockProvider()
        results = []
        async for chunk in p.stream_json("test", {"type": "object", "properties": {"x": {"type": "integer"}}}):
            results.append(chunk)
        assert len(results) >= 1
        assert "x" in results[0]
