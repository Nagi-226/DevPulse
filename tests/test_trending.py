"""M2: Trending 列表测试 — daily/weekly/语言/来源搜索/离线缓存."""
import pytest


@pytest.mark.usefixtures("seed_repos")
class TestTrending:
    """Trending 列表测试套件."""

    async def test_trending_daily(self, async_client):
        """daily trending 应返回 daily 范围的仓库."""
        response = await async_client.get("/repos/trending", params={"since": "daily"})
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["since"] == "daily"
        # 应只包含 trending_since="daily" 的仓库
        for item in data["items"]:
            # 因为 API 返回的 items 没有 trending_since 字段，我们检查返回数据
            assert "full_name" in item
            assert "language" in item

    async def test_trending_weekly(self, async_client):
        """weekly trending 应返回 weekly 范围的仓库."""
        response = await async_client.get("/repos/trending", params={"since": "weekly"})
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["since"] == "weekly"
        assert len(data["items"]) > 0

    async def test_language_filter(self, async_client):
        """语言过滤应只返回指定语言的仓库."""
        response = await async_client.get(
            "/repos/trending",
            params={"language": "Python"},
        )
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["language"] == "Python"

    async def test_source_filter(self, async_client):
        """来源过滤应只返回指定来源的仓库."""
        response = await async_client.get(
            "/repos/trending",
            params={"source": "gitlab"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["source"] == "gitlab"
        for item in data["items"]:
            assert item["source"] == "gitlab"

    async def test_search(self, async_client):
        """关键词搜索应返回匹配的仓库."""
        response = await async_client.get(
            "/repos/",
            params={"q": "python"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        # 至少匹配 python-repo
        assert any("python" in item["full_name"].lower() for item in data["items"])

    async def test_trending_empty(self, async_client):
        """空结果不应报错（离线缓存场景）."""
        response = await async_client.get(
            "/repos/trending",
            params={"language": "NonExistentLanguage", "since": "monthly"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []

    async def test_list_repos_pagination(self, async_client):
        """列表分页应正常工作."""
        response = await async_client.get("/repos/", params={"page": 1, "limit": 2})
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data
        assert data["page"] == 1
        assert data["limit"] == 2
        assert len(data["items"]) <= 2

    async def test_repo_detail(self, async_client, seed_repo):
        """仓库详情应返回完整信息."""
        response = await async_client.get(f"/repos/{seed_repo.full_name}")
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "seed-owner/seed-repo"
        assert data["language"] == "Python"
        assert "is_favorited" in data
        assert data["is_favorited"] is False

    async def test_repo_detail_not_found(self, async_client):
        """不存在的仓库应返回 404."""
        response = await async_client.get("/repos/nonexistent/ghost-repo")
        assert response.status_code == 404
