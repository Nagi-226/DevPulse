"""M6/M9: 健康检查 + 基础端点测试."""
import pytest


class TestHealth:
    """健康检查端点测试."""

    async def test_health_endpoint(self, async_client):
        """GET /health 应返回 200 及状态信息."""
        response = await async_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "db_status" in data
        assert "last_weekly_report" in data

    async def test_health_detailed(self, async_client):
        """GET /health/detailed 应返回详细健康状态."""
        response = await async_client.get("/health/detailed")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["db_status"] == "connected"
        assert "version" in data

    async def test_api_docs_available(self, async_client):
        """OpenAPI docs 应可访问."""
        response = await async_client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert data["info"]["title"] == "DevPulse"
        # 验证关键端点都在 docs 中
        paths = list(data["paths"].keys())
        assert any("auth" in p for p in paths)
        assert any("repos" in p for p in paths)
        assert any("admin" in p for p in paths)

    async def test_privacy_policy(self, async_client):
        """GET /privacy 应返回 HTML 隐私政策页面."""
        response = await async_client.get("/privacy")
        assert response.status_code == 200
        content_type = response.headers.get("content-type", "")
        assert "html" in content_type
        content = response.text
        assert "隐私政策" in content
        assert "DevPulse" in content

    async def test_root_not_found(self, async_client):
        """GET / 根路径可能返回 404（没有根路由）."""
        response = await async_client.get("/")
        # 根路径可能不存在或返回 404
        assert response.status_code in (200, 404)
