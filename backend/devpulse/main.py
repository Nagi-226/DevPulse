"""DevPulse FastAPI 应用入口."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from devpulse import __version__
from devpulse.api.endpoints.repos import router as repos_router
from devpulse.api.endpoints.scheduler import router as scheduler_router
from devpulse.config import settings
from devpulse.core.database import Database
from devpulse.services.scheduler import DevPulseScheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动时初始化数据库与调度器，关闭时释放资源."""
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

    if settings.SCHEDULER_ENABLED:
        scheduler = DevPulseScheduler()
        scheduler.add_weekly_job(
            day_of_week=settings.SCHEDULER_CRON_DAY,
            hour=settings.SCHEDULER_CRON_HOUR,
            minute=settings.SCHEDULER_CRON_MINUTE,
        )
        scheduler.start()
        app.state.scheduler = scheduler

    yield

    # Shutdown
    scheduler = getattr(app.state, "scheduler", None)
    if scheduler:
        scheduler.shutdown()
    db = getattr(app.state, "db", None)
    if db:
        await db.close()


app = FastAPI(
    title="DevPulse",
    description="AI 潮汐 — GitHub Trending AI/ML 周报引擎",
    version=__version__,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载仓库与周报 API 路由
app.include_router(repos_router)
app.include_router(scheduler_router)


@app.get("/health")
async def health() -> dict[str, str]:
    """健康检查端点."""
    return {"status": "ok", "version": __version__}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("devpulse.main:app", host="127.0.0.1", port=8000, reload=True)
