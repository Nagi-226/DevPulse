"""DevPulse FastAPI 应用入口."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from devpulse import __version__
from devpulse.api.endpoints.repos import router as repos_router
from devpulse.config import settings
from devpulse.core.database import Database


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动时初始化数据库，关闭时释放资源."""
    # Startup
    db = Database(
        url=settings.DATABASE_URL,
        echo=settings.DATABASE_ECHO,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
    )
    await db.create_tables()
    app.state.db = db
    app.state.settings = settings

    yield

    # Shutdown
    await db.close()


app = FastAPI(
    title="DevPulse",
    description="AI 潮汐 — GitHub Trending AI/ML 周报引擎",
    version=__version__,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:1420", "tauri://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载仓库与周报 API 路由
app.include_router(repos_router)


@app.get("/health")
async def health() -> dict[str, str]:
    """健康检查端点."""
    return {"status": "ok", "version": __version__}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("devpulse.main:app", host="127.0.0.1", port=8000, reload=True)
