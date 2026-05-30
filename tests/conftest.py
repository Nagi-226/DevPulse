"""DevPulse 测试基础设施 — 共享 fixtures.

关键设计:
  1. app fixture 先 monkeypatch settings，再导入模块级 app 对象
  2. test_db 使用独立的 SQLite :memory: 数据库
  3. async_client 在 app 上设置 test_db，然后通过 ASGITransport 创建客户端
"""

import sys
from pathlib import Path

# 将 backend/ 加入 sys.path，使得 `from devpulse.xxx` 导入可用
_backend_dir = str(Path(__file__).resolve().parent.parent / "backend")
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient


def pytest_configure(config):
    """强制 asyncio auto 模式，使 async 测试/类方法无需显式标记 @pytest.mark.asyncio."""
    config.option.asyncio_mode = "auto"

# 仅检查基础依赖是否可用，不导入 app（避免提前使用原始配置）
_BACKEND_AVAILABLE = False
try:
    import fastapi  # noqa: F401
    import sqlalchemy  # noqa: F401
    import aiosqlite  # noqa: F401
    import passlib  # noqa: F401
    import jwt as _pyjwt  # noqa: F401

    _BACKEND_AVAILABLE = True
except ImportError:
    pass


@pytest.fixture
def app(monkeypatch):
    """创建 FastAPI 测试 app 实例.

    必须在 monkeypatch settings 之后才导入 app。
    禁用 lifespan 以便 test_db 完全接管数据库管理。
    """
    if not _BACKEND_AVAILABLE:
        pytest.skip("Backend dependencies not installed")

    from contextlib import asynccontextmanager

    from backend.devpulse import config

    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setattr(config.settings, "DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setattr(config.settings, "SCHEDULER_ENABLED", False)
    monkeypatch.setattr(config.settings, "SENTRY_DSN", "")

    # 现在才导入 app
    from backend.devpulse.main import app as _app

    # 用空 lifespan 替换原有 lifespan，避免创建第二个 :memory: 数据库
    @asynccontextmanager
    async def _empty_lifespan(app_instance):
        yield

    _app.router.lifespan_context = _empty_lifespan

    return _app


@pytest_asyncio.fixture
async def test_db():
    """SQLite :memory: 测试数据库."""
    if not _BACKEND_AVAILABLE:
        pytest.skip("Backend dependencies not installed")

    from backend.devpulse.core.database import Database

    db = Database("sqlite+aiosqlite:///:memory:")
    await db.create_tables()
    yield db
    await db.drop_tables()
    await db.close()


@pytest_asyncio.fixture
async def async_client(app, test_db):
    """httpx AsyncClient，通过 ASGITransport 直接测试 ASGI app.

    在创建 transport 之前设置 app.state.db = test_db。
    注意：lifespan 启动时会再次设置 app.state.db（创建 SQLite :memory: DB），
    但因为我们 monkeypatched DATABASE_URL 为 :memory:，lifespan 创建的也是 :memory: DB，
    不会造成冲突。
    """
    if not _BACKEND_AVAILABLE:
        pytest.skip("Backend dependencies not installed")

    app.state.db = test_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# ── Auth fixtures ────────────────────────────────────────────

@pytest_asyncio.fixture
async def auth_headers(async_client, test_db):
    """注册普通用户 → 登录 → 返回 Authorization header."""
    response = await async_client.post("/auth/register", json={
        "email": "test-auth@example.com",
        "password": "Test1234",
        "confirm_password": "Test1234",
        "display_name": "Test Auth User",
    })
    assert response.status_code == 200, f"Register failed: {response.text}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def admin_headers(async_client, test_db):
    """注册 admin 用户 → 手动提升角色 → 返回 Authorization header."""
    response = await async_client.post("/auth/register", json={
        "email": "admin-test@example.com",
        "password": "Admin1234",
        "confirm_password": "Admin1234",
        "display_name": "Admin Test User",
    })
    assert response.status_code == 200, f"Admin register failed: {response.text}"
    token = response.json()["access_token"]

    # 手动将用户角色升级为 admin
    from backend.devpulse.core.models import User
    from sqlalchemy import select

    async with test_db.get_session() as session:
        result = await session.execute(
            select(User).where(User.email == "admin-test@example.com")
        )
        user = result.scalar_one_or_none()
        assert user is not None
        user.role = "admin"  # type: ignore[assignment]
        await session.commit()

    return {"Authorization": f"Bearer {token}"}


# ── Seed fixtures ────────────────────────────────────────────

@pytest_asyncio.fixture
async def seed_user(test_db):
    """预置一个普通用户（直接 DB 写入）."""
    from backend.devpulse.core.models import User
    from backend.devpulse.services.auth_service import auth_service

    async with test_db.get_session() as session:
        user = User(
            email="seed@example.com",
            password_hash=auth_service.hash_password("Seed1234"),
            display_name="Seed User",
            role="user",
            is_active=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


@pytest_asyncio.fixture
async def seed_repo(test_db):
    """预置一个仓库."""
    from backend.devpulse.core.models import Repository

    async with test_db.get_session() as session:
        repo = Repository(
            full_name="seed-owner/seed-repo",
            owner="seed-owner",
            name="seed-repo",
            description="A seeded test repository",
            language="Python",
            topics=["ml", "ai"],
            total_stars=1000,
            stars_since=100,
            forks=200,
            forks_since=20,
            open_issues=5,
            trending_rank=1,
            trending_since="weekly",
            source="github",
            review_status="approved",
            confidence_score=0.95,
        )
        session.add(repo)
        await session.commit()
        await session.refresh(repo)
        return repo


@pytest_asyncio.fixture
async def seed_repos(test_db):
    """预置多个仓库（涵盖不同语言和来源）."""
    from backend.devpulse.core.models import Repository

    repos_data = [
        dict(full_name="owner1/python-repo", owner="owner1", name="python-repo",
             description="A Python ML library", language="Python",
             total_stars=5000, stars_since=200, trending_rank=1, trending_since="weekly",
             source="github", review_status="approved"),
        dict(full_name="owner2/js-repo", owner="owner2", name="js-repo",
             description="A JavaScript framework", language="JavaScript",
             total_stars=3000, stars_since=150, trending_rank=2, trending_since="weekly",
             source="github", review_status="approved"),
        dict(full_name="owner3/go-repo", owner="owner3", name="go-repo",
             description="A Go tool", language="Go",
             total_stars=2000, stars_since=100, trending_rank=3, trending_since="daily",
             source="github", review_status="approved"),
        dict(full_name="owner4/gitlab-repo", owner="owner4", name="gitlab-repo",
             description="A GitLab project", language="Rust",
             total_stars=800, stars_since=50, trending_rank=4, trending_since="weekly",
             source="gitlab", review_status="pending"),
        dict(full_name="owner5/pending-repo", owner="owner5", name="pending-repo",
             description="Pending review repo", language="TypeScript",
             total_stars=600, stars_since=30, trending_rank=5, trending_since="weekly",
             source="github", review_status="pending", confidence_score=0.5,
             review_required=True),
        dict(full_name="owner6/rejected-repo", owner="owner6", name="rejected-repo",
             description="Rejected repo", language="Java",
             total_stars=400, stars_since=10, trending_rank=6, trending_since="weekly",
             source="github", review_status="rejected"),
    ]

    async with test_db.get_session() as session:
        repos = []
        for data in repos_data:
            repo = Repository(**data)
            session.add(repo)
            repos.append(repo)
        await session.commit()
        for r in repos:
            await session.refresh(r)
        return repos
