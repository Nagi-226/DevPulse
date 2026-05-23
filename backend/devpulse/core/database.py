"""数据库引擎与连接池管理 — 支持 SQLite 和 PostgreSQL 双引擎."""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from devpulse.core.models import Base

logger = logging.getLogger(__name__)


class Database:
    """异步数据库连接管理器.

    封装 SQLAlchemy 2.0 AsyncEngine，支持 SQLite 和 PostgreSQL 双引擎。
    通过连接字符串前缀自动识别引擎类型。

    Args:
        url: SQLAlchemy 异步连接字符串.
        echo: 是否打印 SQL 日志.
        pool_size: 连接池大小（PostgreSQL 有效）.
        max_overflow: 连接池最大溢出数（PostgreSQL 有效）.
    """

    def __init__(
        self,
        url: str,
        echo: bool = False,
        pool_size: int = 5,
        max_overflow: int = 10,
    ) -> None:
        self._url = url
        self._echo = echo
        self._pool_size = pool_size
        self._max_overflow = max_overflow

        # SQLite 不支持 pool_size/max_overflow
        if "sqlite" in url:
            self._engine: AsyncEngine = create_async_engine(url, echo=echo)
        else:
            self._engine = create_async_engine(
                url,
                echo=echo,
                pool_size=pool_size,
                max_overflow=max_overflow,
            )

        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        logger.info("Database engine created: %s", self._mask_url(url))

    async def create_tables(self) -> None:
        """创建所有 ORM 映射的数据表（已有表则跳过）."""
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")

    async def drop_tables(self) -> None:
        """删除所有 ORM 映射的数据表（仅开发/测试用）."""
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.warning("Database tables dropped")

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """获取异步会话上下文管理器.

        Yields:
            AsyncSession: 用于数据库操作的异步会话.
        """
        async with self._session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def close(self) -> None:
        """关闭数据库引擎，释放连接池."""
        await self._engine.dispose()
        logger.info("Database engine disposed")

    @staticmethod
    def create_sqlite_url(path: str = "./devpulse.db") -> str:
        """生成 SQLite 异步连接字符串.

        Args:
            path: 数据库文件路径，默认 ./devpulse.db.

        Returns:
            形如 ``sqlite+aiosqlite:///./devpulse.db`` 的连接字符串.
        """
        return f"sqlite+aiosqlite:///{path}"

    @staticmethod
    def create_postgres_url(
        user: str,
        password: str,
        host: str,
        port: int,
        db: str,
    ) -> str:
        """生成 PostgreSQL 异步连接字符串.

        Args:
            user: 数据库用户名.
            password: 数据库密码.
            host: 主机地址.
            port: 端口号.
            db: 数据库名.

        Returns:
            形如 ``postgresql+asyncpg://user:pass@host:port/db`` 的连接字符串.
        """
        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"

    @staticmethod
    def _mask_url(url: str) -> str:
        """隐藏连接字符串中的密码."""
        import re

        return re.sub(r"://[^:]+:[^@]+@", "://***:***@", url)
