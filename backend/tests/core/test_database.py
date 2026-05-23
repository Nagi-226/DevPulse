"""数据库引擎与连接池单元测试."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from devpulse.core.database import Database


def test_sqlite_url_generation():
    """验证 SQLite 连接字符串生成."""
    url = Database.create_sqlite_url("./test.db")
    assert url == "sqlite+aiosqlite:///./test.db"

    url2 = Database.create_sqlite_url("C:/data/devpulse.db")
    assert url2 == "sqlite+aiosqlite:///C:/data/devpulse.db"


def test_postgres_url_generation():
    """验证 PostgreSQL 连接字符串生成."""
    url = Database.create_postgres_url(
        user="devpulse",
        password="secret123",
        host="localhost",
        port=5432,
        db="devpulse",
    )
    assert url == "postgresql+asyncpg://devpulse:secret123@localhost:5432/devpulse"

    # 特殊字符测试
    url2 = Database.create_postgres_url(
        user="user@domain",
        password="p@ssw0rd#",
        host="db.example.com",
        port=5433,
        db="test-db",
    )
    assert url2 == "postgresql+asyncpg://user@domain:p@ssw0rd#@db.example.com:5433/test-db"


@pytest.mark.asyncio
async def test_create_tables():
    """验证建表成功（不依赖真实数据库）."""
    # 使用内存 SQLite 避免文件 I/O
    db = Database("sqlite+aiosqlite:///:memory:", echo=False)
    try:
        # 不应抛出异常
        await db.create_tables()
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_session_context():
    """验证会话上下文管理器正常工作."""
    db = Database("sqlite+aiosqlite:///:memory:")
    try:
        async with db.get_session() as session:
            assert isinstance(session, AsyncSession)
            # 会话应处于活动状态
            assert session.in_transaction() is False  # 未开始事务
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_drop_tables():
    """验证删表功能（仅开发用）."""
    db = Database("sqlite+aiosqlite:///:memory:")
    try:
        await db.create_tables()
        # 再次调用不应出错（表已存在）
        await db.create_tables()
        await db.drop_tables()
        # 删表后可重新建表
        await db.create_tables()
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_close_engine():
    """验证引擎关闭释放资源."""
    db = Database("sqlite+aiosqlite:///:memory:")
    # 创建会话工厂
    async with db.get_session() as session:
        assert session.is_active

    await db.close()
    # 关闭后不应再使用，但无直接 API 检查


def test_mask_url():
    """验证连接字符串密码脱敏."""
    # 直接调用私有方法（测试需要）
    url = "postgresql+asyncpg://user:password@localhost:5432/db"
    masked = Database._mask_url(url)
    assert "://***:***@" in masked
    assert "user" not in masked
    assert "password" not in masked

    # SQLite 无密码
    url2 = "sqlite+aiosqlite:///./test.db"
    masked2 = Database._mask_url(url2)
    assert url2 == masked2

    # 复杂密码
    url3 = "postgresql+asyncpg://admin:p@ssw0rd#123@db.example.com:5432/db"
    masked3 = Database._mask_url(url3)
    assert "://***:***@" in masked3
    assert "p@ssw0rd#123" not in masked3
