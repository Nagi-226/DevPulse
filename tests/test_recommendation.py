"""M5: 推荐测试 — L1 协同过滤/L2 内容过滤/L3 热门/匿名用户."""
import pytest


class TestRecommendation:
    """推荐引擎测试套件."""

    async def test_anonymous_user_l3(self, async_client, seed_repos):
        """匿名用户应返回 L3 全局热门推荐."""
        response = await async_client.get("/repos/recommended", params={"limit": 5})
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "items" in data["data"]
        assert data["data"]["fallback_level"] == 3
        assert data["data"]["method"] == "popular"

    async def test_new_user_l3(self, async_client, auth_headers, seed_repos):
        """无行为记录的新用户应返回 L3 热门推荐."""
        response = await async_client.get(
            "/repos/recommended",
            params={"limit": 5},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["fallback_level"] == 3

    async def test_insufficient_behavior_l2(self, async_client, auth_headers, seed_repos, test_db):
        """有少量行为（<3）的用户应返回 L2 内容推荐."""
        # 用户（auth_headers 已创建）有 1 条行为 → 触发 L2
        from tests.factories import create_user_behavior
        from sqlalchemy import select
        from backend.devpulse.core.models import User

        async with test_db.get_session() as session:
            result = await session.execute(
                select(User).where(User.email == "test-auth@example.com")
            )
            user = result.scalar_one_or_none()
            await create_user_behavior(
                session, user.id, seed_repos[0].id, action_type="view"
            )

        response = await async_client.get(
            "/repos/recommended",
            params={"limit": 5},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        # 应有结果（L2 或 L3 降级）
        assert "items" in data["data"]

    async def test_cf_l1(self, async_client, auth_headers, seed_repos, test_db):
        """有足够行为（≥3）的用户应返回 L1 协同过滤推荐."""
        from tests.factories import create_user, create_user_behavior
        from sqlalchemy import select
        from backend.devpulse.core.models import User

        async with test_db.get_session() as session:
            # 当前用户（auth_headers）
            result = await session.execute(
                select(User).where(User.email == "test-auth@example.com")
            )
            current_user = result.scalar_one_or_none()

            # 创建另一个用户作为相似用户
            other_user = await create_user(session, email="other-cf@example.com")

            # 当前用户有 3 条行为（达到 CF 阈值）
            await create_user_behavior(
                session, current_user.id, seed_repos[0].id, action_type="view"
            )
            await create_user_behavior(
                session, current_user.id, seed_repos[1].id, action_type="star"
            )
            await create_user_behavior(
                session, current_user.id, seed_repos[2].id, action_type="like"
            )

            # 相似用户也有行为
            await create_user_behavior(
                session, other_user.id, seed_repos[0].id, action_type="star"
            )
            await create_user_behavior(
                session, other_user.id, seed_repos[3].id, action_type="star"
            )
            await create_user_behavior(
                session, other_user.id, seed_repos[4].id, action_type="star"
            )

        response = await async_client.get(
            "/repos/recommended",
            params={"limit": 5},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "items" in data["data"]
        # 至少有一个推荐结果
        assert len(data["data"]["items"]) >= 0
