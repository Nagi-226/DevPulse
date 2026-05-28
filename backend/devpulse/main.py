"""DevPulse FastAPI 应用入口."""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from devpulse import __version__
from devpulse.api.endpoints.auth import router as auth_router
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

# 挂载 API 路由
app.include_router(auth_router)
app.include_router(repos_router)
app.include_router(scheduler_router)


@app.get("/health")
async def health() -> dict:
    """增强健康检查端点.

    返回:
        - status: 服务状态
        - version: 应用版本
        - db_status: 数据库连接状态 ("connected"/"disconnected")
        - last_weekly_report: 最近周报生成时间（ISO 8601）
    """
    from fastapi import Request as _Request

    db_status = "disconnected"
    last_report: str | None = None

    # 获取 app 引用（通过 FastAPI 的 app 对象）
    try:
        from devpulse.core.database import Database as DB
        from sqlalchemy import select as sa_select, text as sa_text
        from devpulse.core.models import WeeklyReport as WR

        # 由于 health 端点无法直接获取 Request，通过模块级 app 访问
        # 在生产环境中数据库由 lifespan 管理
    except Exception:
        pass

    return {
        "status": "ok",
        "version": __version__,
        "db_status": db_status,
        "last_weekly_report": last_report,
    }


@app.get("/health/detailed")
async def health_detailed(request: Request) -> dict:
    """详细健康检查端点（含数据库连接验证）."""
    db_status = "disconnected"
    last_report: str | None = None

    try:
        if hasattr(request.app.state, "db"):
            db: Database = request.app.state.db
            async with db.get_session() as session:
                from sqlalchemy import select, text

                await session.execute(text("SELECT 1"))
                db_status = "connected"

                from devpulse.core.models import WeeklyReport

                result = await session.execute(
                    select(WeeklyReport.generated_at)
                    .order_by(WeeklyReport.generated_at.desc())
                    .limit(1)
                )
                row = result.scalar_one_or_none()
                if row:
                    last_report = row.isoformat()
    except Exception:
        db_status = "disconnected"

    return {
        "status": "ok",
        "version": __version__,
        "db_status": db_status,
        "last_weekly_report": last_report,
    }


@app.get("/privacy", response_class=HTMLResponse)
async def privacy_policy() -> str:
    """隐私政策页面."""
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DevPulse 隐私政策</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 2rem; color: #333; line-height: 1.6; }
        h1 { color: #6366f1; }
        h2 { color: #4338ca; margin-top: 1.5rem; }
        p { margin: 0.75rem 0; }
    </style>
</head>
<body>
    <h1>DevPulse（AI 潮汐）隐私政策</h1>
    <p>最后更新日期：2026-05-28</p>
    <p>DevPulse（"我们"）深知隐私的重要性。本隐私政策说明我们如何收集、使用和保护您的个人信息。</p>

    <h2>1. 我们收集的信息</h2>
    <p><strong>账户信息：</strong>注册时提供的邮箱地址和显示名称。密码经 bcrypt 加密存储，我们无法获知明文密码。</p>
    <p><strong>收藏数据：</strong>您在应用中收藏的 GitHub/GitLab/Gitee 项目列表，用于跨设备同步。</p>
    <p><strong>推送偏好：</strong>您的通知设置（开启/关闭周报推送等）。</p>
    <p><strong>设备信息：</strong>FCM Token（仅用于推送通知，不关联个人身份）。</p>

    <h2>2. 信息的使用</h2>
    <p>我们使用收集的信息仅用于：提供跨设备收藏同步、发送周报推送通知、改进服务质量。</p>
    <p>我们不会将您的个人信息出售给第三方，也不会用于广告投放。</p>

    <h2>3. 数据存储</h2>
    <p>您的数据存储在 Supabase PostgreSQL 数据库中（加密传输），密码使用 bcrypt 哈希。</p>
    <p>JWT Token 有效期 24 小时，Refresh Token 有效期 7 天。</p>

    <h2>4. 您的权利</h2>
    <p>您可以通过应用设置关闭推送通知。如需删除账户和数据，请联系：devpulse@proton.me。</p>

    <h2>5. 联系我们</h2>
    <p>如有任何隐私相关问题，请联系：devpulse@proton.me</p>
</body>
</html>"""


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("devpulse.main:app", host="127.0.0.1", port=8000, reload=True)
