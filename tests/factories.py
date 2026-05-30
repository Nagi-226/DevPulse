"""测试数据工厂 — 快速创建 ORM 对象."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from backend.devpulse.core.models import (
    Comment,
    DailyStats,
    Favorite,
    Like,
    Repository,
    User,
    UserBehavior,
)
from backend.devpulse.services.auth_service import auth_service


async def create_user(session: Any, **kwargs) -> User:
    """创建测试用户.

    Args:
        session: SQLAlchemy 异步 session.
        **kwargs: 覆盖默认字段，包括 email, password, display_name, role, is_active.

    Returns:
        已持久化的 User 对象.
    """
    email = kwargs.pop("email", f"factory-{_random_suffix()}@example.com")
    password = kwargs.pop("password", "Factory1234")
    display_name = kwargs.pop("display_name", "Factory User")
    role = kwargs.pop("role", "user")
    is_active = kwargs.pop("is_active", True)

    user = User(
        email=email,
        password_hash=auth_service.hash_password(password),
        display_name=display_name,
        role=role,
        is_active=is_active,
        created_at=kwargs.pop("created_at", datetime.now(timezone.utc)),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def create_repo(session: Any, **kwargs) -> Repository:
    """创建测试仓库.

    Args:
        session: SQLAlchemy 异步 session.
        **kwargs: 覆盖默认字段.

    Returns:
        已持久化的 Repository 对象.
    """
    full_name = kwargs.pop("full_name", f"factory-owner/factory-repo-{_random_suffix()}")
    parts = full_name.split("/") if "/" in full_name else ["factory-owner", full_name]

    defaults: dict[str, Any] = dict(
        full_name=full_name,
        owner=parts[0],
        name=parts[1],
        description=kwargs.pop("description", "A factory test repository"),
        language=kwargs.pop("language", "Python"),
        topics=kwargs.pop("topics", ["test"]),
        total_stars=kwargs.pop("total_stars", 100),
        stars_since=kwargs.pop("stars_since", 10),
        forks=kwargs.pop("forks", 20),
        forks_since=kwargs.pop("forks_since", 2),
        open_issues=kwargs.pop("open_issues", 3),
        trending_rank=kwargs.pop("trending_rank", 99),
        trending_since=kwargs.pop("trending_since", "weekly"),
        source=kwargs.pop("source", "github"),
        review_status=kwargs.pop("review_status", "approved"),
        confidence_score=kwargs.pop("confidence_score", 0.9),
        url=kwargs.pop("url", f"https://github.com/{full_name}"),
    )
    defaults.update(kwargs)

    repo = Repository(**defaults)
    session.add(repo)
    await session.commit()
    await session.refresh(repo)
    return repo


async def create_comment(session: Any, user_id: int, repo_id: int, **kwargs) -> Comment:
    """创建测试评论.

    Args:
        session: SQLAlchemy 异步 session.
        user_id: 评论者 ID.
        repo_id: 仓库 ID.
        **kwargs: 覆盖默认字段.

    Returns:
        已持久化的 Comment 对象.
    """
    comment = Comment(
        user_id=user_id,
        repo_id=repo_id,
        content=kwargs.pop("content", "This is a test comment."),
        parent_id=kwargs.pop("parent_id", None),
        is_deleted=kwargs.pop("is_deleted", False),
        created_at=kwargs.pop("created_at", datetime.now(timezone.utc)),
    )
    session.add(comment)
    await session.commit()
    await session.refresh(comment)
    return comment


async def create_like(session: Any, user_id: int, repo_id: int, **kwargs) -> Like:
    """创建测试点赞.

    Args:
        session: SQLAlchemy 异步 session.
        user_id: 点赞者 ID.
        repo_id: 仓库 ID.
        **kwargs: 覆盖默认字段.

    Returns:
        已持久化的 Like 对象.
    """
    like = Like(
        user_id=user_id,
        repo_id=repo_id,
        created_at=kwargs.pop("created_at", datetime.now(timezone.utc)),
    )
    session.add(like)
    await session.commit()
    await session.refresh(like)
    return like


async def create_favorite(session: Any, user_id: int, repo_id: int, **kwargs) -> Favorite:
    """创建测试收藏.

    Args:
        session: SQLAlchemy 异步 session.
        user_id: 收藏者 ID.
        repo_id: 仓库 ID.
        **kwargs: 覆盖默认字段.

    Returns:
        已持久化的 Favorite 对象.
    """
    favorite = Favorite(
        user_id=user_id,
        repo_id=repo_id,
        created_at=kwargs.pop("created_at", datetime.now(timezone.utc)),
    )
    session.add(favorite)
    await session.commit()
    await session.refresh(favorite)
    return favorite


async def create_user_behavior(
    session: Any, user_id: int, repo_id: int, action_type: str = "view", **kwargs
) -> UserBehavior:
    """创建测试用户行为记录.

    Args:
        session: SQLAlchemy 异步 session.
        user_id: 用户 ID.
        repo_id: 仓库 ID.
        action_type: 行为类型 (view/star/like/share/comment).
        **kwargs: 覆盖默认字段.

    Returns:
        已持久化的 UserBehavior 对象.
    """
    behavior = UserBehavior(
        user_id=user_id,
        repo_id=repo_id,
        action_type=action_type,
        weight=kwargs.pop("weight", 1.0),
        created_at=kwargs.pop("created_at", datetime.now(timezone.utc)),
    )
    session.add(behavior)
    await session.commit()
    await session.refresh(behavior)
    return behavior


def _random_suffix() -> str:
    """生成短随机后缀."""
    import random
    import string
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
