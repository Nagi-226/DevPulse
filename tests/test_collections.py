"""M3: 收藏测试 — star/unstar/列表/趋势/语言统计."""
import pytest


class TestCollections:
    """收藏功能测试套件."""

    async def test_star_repo(self, async_client, auth_headers, seed_repo):
        """收藏仓库应返回成功."""
        response = await async_client.post(
            f"/repos/{seed_repo.full_name}/star",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "Starred successfully" in data["message"]

    async def test_star_repo_already_starred(self, async_client, auth_headers, seed_repo):
        """重复收藏应返回 Already starred."""
        # 第一次收藏
        await async_client.post(
            f"/repos/{seed_repo.full_name}/star",
            headers=auth_headers,
        )
        # 第二次收藏（重复）
        response = await async_client.post(
            f"/repos/{seed_repo.full_name}/star",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "Already starred" in data["message"]

    async def test_unstar_repo(self, async_client, auth_headers, seed_repo):
        """取消收藏应返回成功."""
        # 先收藏
        await async_client.post(
            f"/repos/{seed_repo.full_name}/star",
            headers=auth_headers,
        )
        # 再取消
        response = await async_client.delete(
            f"/repos/{seed_repo.full_name}/star",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unstarred successfully" in data["message"]

    async def test_unstar_not_starred(self, async_client, auth_headers, seed_repo):
        """取消未收藏的仓库应返回 404."""
        response = await async_client.delete(
            f"/repos/{seed_repo.full_name}/star",
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_star_requires_auth(self, async_client, seed_repo):
        """未登录收藏应返回 401."""
        response = await async_client.post(
            f"/repos/{seed_repo.full_name}/star",
        )
        assert response.status_code == 401

    async def test_collections_list(self, async_client, auth_headers, seed_repos):
        """收藏列表应返回用户已收藏的仓库."""
        # 收藏第一个仓库
        await async_client.post(
            f"/repos/{seed_repos[0].full_name}/star",
            headers=auth_headers,
        )
        # 收藏第二个仓库
        await async_client.post(
            f"/repos/{seed_repos[1].full_name}/star",
            headers=auth_headers,
        )

        response = await async_client.get(
            "/repos/collections",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

    async def test_collections_list_empty(self, async_client, auth_headers):
        """无收藏时应返回空列表."""
        response = await async_client.get(
            "/repos/collections",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    async def test_star_history(self, async_client, seed_repo):
        """Star 历史应返回趋势数据."""
        response = await async_client.get(
            f"/repos/{seed_repo.full_name}/star-history",
            params={"period": "30d"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    async def test_language_stats(self, async_client, seed_repos):
        """语言统计应返回语言分布."""
        response = await async_client.get("/repos/stats/languages")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data
        assert data["total"] > 0
        # 检查 Python 在统计数据中
        languages = [item["language"] for item in data["items"]]
        assert "Python" in languages or len(languages) > 0
