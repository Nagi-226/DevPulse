"""M4: 互动测试 — 评论 CRUD/点赞 Toggle/互动统计."""
import pytest


class TestComments:
    """评论测试套件."""

    async def test_create_comment(self, async_client, auth_headers, seed_repo):
        """发表评论应返回成功."""
        response = await async_client.post(
            f"/repos/{seed_repo.full_name}/comments",
            json={"content": "Great project!"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["content"] == "Great project!"

    async def test_create_comment_empty(self, async_client, auth_headers, seed_repo):
        """空评论应返回 422."""
        response = await async_client.post(
            f"/repos/{seed_repo.full_name}/comments",
            json={"content": ""},
            headers=auth_headers,
        )
        assert response.status_code == 422
        assert "不能为空" in response.json()["detail"]

    async def test_create_comment_too_long(self, async_client, auth_headers, seed_repo):
        """超过 2000 字的评论应返回 422."""
        response = await async_client.post(
            f"/repos/{seed_repo.full_name}/comments",
            json={"content": "x" * 2001},
            headers=auth_headers,
        )
        assert response.status_code == 422
        assert "2000" in response.json()["detail"]

    async def test_get_comments(self, async_client, auth_headers, seed_repo):
        """获取评论列表应返回评论."""
        # 先发表评论
        await async_client.post(
            f"/repos/{seed_repo.full_name}/comments",
            json={"content": "Comment one"},
            headers=auth_headers,
        )
        await async_client.post(
            f"/repos/{seed_repo.full_name}/comments",
            json={"content": "Comment two"},
            headers=auth_headers,
        )

        response = await async_client.get(
            f"/repos/{seed_repo.full_name}/comments",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["total"] == 2
        assert len(data["data"]["items"]) == 2

    async def test_get_comments_empty(self, async_client, seed_repo):
        """无评论时应返回空列表."""
        response = await async_client.get(
            f"/repos/{seed_repo.full_name}/comments",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total"] == 0
        assert data["data"]["items"] == []

    async def test_delete_own_comment(self, async_client, auth_headers, seed_repo):
        """删除自己的评论应返回成功."""
        # 发表评论
        create_resp = await async_client.post(
            f"/repos/{seed_repo.full_name}/comments",
            json={"content": "To be deleted"},
            headers=auth_headers,
        )
        comment_id = create_resp.json()["data"]["id"]

        response = await async_client.delete(
            f"/repos/{seed_repo.full_name}/comments/{comment_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["deleted"] is True

        # 确认软删除后不在列表中
        list_resp = await async_client.get(
            f"/repos/{seed_repo.full_name}/comments",
        )
        assert list_resp.json()["data"]["total"] == 0

    async def test_delete_others_comment_normal_user(self, async_client, auth_headers, seed_repo, test_db):
        """普通用户删除他人评论应返回 403."""
        # 用 seed_user 发表评论（factory user）
        from tests.factories import create_comment, create_user

        async with test_db.get_session() as session:
            other_user = await create_user(session, email="other@example.com")
            comment = await create_comment(session, other_user.id, seed_repo.id, content="Other's comment")

        response = await async_client.delete(
            f"/repos/{seed_repo.full_name}/comments/{comment.id}",
            headers=auth_headers,
        )
        assert response.status_code == 403

    async def test_admin_delete_comment(self, async_client, admin_headers, seed_repo, test_db):
        """管理员删除他人评论应返回成功."""
        from tests.factories import create_comment, create_user

        async with test_db.get_session() as session:
            other_user = await create_user(session, email="victim@example.com")
            comment = await create_comment(session, other_user.id, seed_repo.id, content="Admin will delete")

        response = await async_client.delete(
            f"/repos/{seed_repo.full_name}/comments/{comment.id}",
            headers=admin_headers,
        )
        assert response.status_code == 200


class TestLikes:
    """点赞测试套件."""

    async def test_toggle_like(self, async_client, auth_headers, seed_repo):
        """首次点赞应返回 liked=True."""
        response = await async_client.post(
            f"/repos/{seed_repo.full_name}/like",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["liked"] is True
        assert data["data"]["count"] == 1

    async def test_toggle_unlike(self, async_client, auth_headers, seed_repo):
        """再次点赞应取消点赞（toggle）."""
        # 第一次点赞
        await async_client.post(
            f"/repos/{seed_repo.full_name}/like",
            headers=auth_headers,
        )
        # 第二次（取消）
        response = await async_client.post(
            f"/repos/{seed_repo.full_name}/like",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["liked"] is False
        assert data["data"]["count"] == 0

    async def test_likes_count(self, async_client, auth_headers, seed_repo):
        """点赞计数应正确反映点赞状态."""
        # 未点赞时
        response = await async_client.get(
            f"/repos/{seed_repo.full_name}/likes-count",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["likes_count"] == 0
        assert data["data"]["is_liked"] is False

        # 点赞后
        await async_client.post(
            f"/repos/{seed_repo.full_name}/like",
            headers=auth_headers,
        )

        response = await async_client.get(
            f"/repos/{seed_repo.full_name}/likes-count",
            headers=auth_headers,
        )
        data = response.json()
        assert data["data"]["likes_count"] == 1
        assert data["data"]["is_liked"] is True


class TestInteractionStats:
    """互动统计测试套件."""

    async def test_get_interactions(self, async_client, auth_headers, seed_repo):
        """互动统计应返回点赞数和评论数."""
        # 发表评论
        await async_client.post(
            f"/repos/{seed_repo.full_name}/comments",
            json={"content": "Stats comment"},
            headers=auth_headers,
        )
        # 点赞
        await async_client.post(
            f"/repos/{seed_repo.full_name}/like",
            headers=auth_headers,
        )

        response = await async_client.get(
            f"/repos/{seed_repo.full_name}/interactions",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["comments_count"] == 1
        assert data["data"]["likes_count"] == 1
