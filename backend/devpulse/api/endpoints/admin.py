"""管理后台 API 端点 — 审核 + Dashboard + 用户管理."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select

from devpulse.api.dependencies import get_admin_user, get_current_user
from devpulse.core.database import Database
from devpulse.core.models import DailyStats, Repository, User
from devpulse.services.review_service import ReviewService
from devpulse.services.stats_service import StatsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


# ═══════════════════════════════════════════════════════════
# 内容审核端点
# ═══════════════════════════════════════════════════════════

@router.get("/pending-reviews")
async def get_pending_reviews(
    request: Request,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(25, ge=1, le=100, description="每页数量"),
    admin_user: dict = Depends(get_admin_user),
) -> dict[str, Any]:
    """获取待审核项目列表 (admin only)."""
    db: Database = request.app.state.db
    async with db.get_session() as session:
        data = await ReviewService.get_pending_reviews(
            session, page=page, page_size=page_size
        )
        return {"code": 0, "message": "success", "data": data}


@router.post("/approve/{repo_id}")
async def approve_review(
    repo_id: int,
    request: Request,
    admin_user: dict = Depends(get_admin_user),
) -> dict[str, Any]:
    """审核通过一个项目 (admin only)."""
    db: Database = request.app.state.db
    async with db.get_session() as session:
        try:
            result = await ReviewService.approve_review(session, repo_id)
            return {"code": 0, "message": "success", "data": result}
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))


@router.post("/reject/{repo_id}")
async def reject_review(
    repo_id: int,
    request: Request,
    admin_user: dict = Depends(get_admin_user),
) -> dict[str, Any]:
    """审核拒绝一个项目 (admin only)."""
    db: Database = request.app.state.db
    async with db.get_session() as session:
        try:
            result = await ReviewService.reject_review(session, repo_id)
            return {"code": 0, "message": "success", "data": result}
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))


@router.get("/reviews/stats")
async def get_review_stats(
    request: Request,
    admin_user: dict = Depends(get_admin_user),
) -> dict[str, Any]:
    """获取审核状态统计 (admin only)."""
    db: Database = request.app.state.db
    async with db.get_session() as session:
        stats = await ReviewService.get_review_stats(session)
        return {"code": 0, "message": "success", "data": stats}


# ═══════════════════════════════════════════════════════════
# Dashboard 看板端点
# ═══════════════════════════════════════════════════════════

@router.get("/dashboard")
async def get_dashboard(
    request: Request,
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    admin_user: dict = Depends(get_admin_user),
) -> dict[str, Any]:
    """获取管理后台 Dashboard 数据 (admin only)."""
    db: Database = request.app.state.db
    async with db.get_session() as session:
        data = await StatsService.get_dashboard_data(session, days=days)
        return {"code": 0, "message": "success", "data": data}


# ═══════════════════════════════════════════════════════════
# 用户管理端点
# ═══════════════════════════════════════════════════════════

@router.get("/users")
async def list_users(
    request: Request,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(25, ge=1, le=100, description="每页数量"),
    q: str = Query("", description="搜索关键词（邮箱/显示名称）"),
    admin_user: dict = Depends(get_admin_user),
) -> dict[str, Any]:
    """获取用户列表 (admin only)."""
    db: Database = request.app.state.db
    async with db.get_session() as session:
        from sqlalchemy import or_

        stmt = select(User).order_by(User.created_at.desc())

        if q:
            like_pattern = f"%{q}%"
            stmt = stmt.where(
                or_(
                    User.email.like(like_pattern),
                    User.display_name.like(like_pattern),
                )
            )

        count_stmt = select(func.count()).select_from(User)
        if q:
            count_stmt = count_stmt.where(
                or_(
                    User.email.like(f"%{q}%"),
                    User.display_name.like(f"%{q}%"),
                )
            )
        total_result = await session.execute(count_stmt)
        total = total_result.scalar() or 0

        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)
        result = await session.execute(stmt)
        users = result.scalars().all()

        items = [
            {
                "id": u.id,
                "email": u.email,
                "display_name": u.display_name,
                "role": getattr(u, "role", "user"),
                "is_active": getattr(u, "is_active", True),
                "push_enabled": u.push_enabled,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ]

        return {
            "code": 0,
            "message": "success",
            "data": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "items": items,
            },
        }


@router.put("/users/{user_id}/ban")
async def toggle_user_ban(
    user_id: int,
    request: Request,
    admin_user: dict = Depends(get_admin_user),
) -> dict[str, Any]:
    """封禁/解禁用户 (admin only).

    Body: {"banned": true/false}
    """
    if user_id == admin_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能封禁自己",
        )

    db: Database = request.app.state.db
    async with db.get_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=404, detail="用户不存在")

        body = await request.json()
        banned = bool(body.get("banned", True))
        user.is_active = not banned

        await session.commit()
        logger.info(
            "Admin %d %s user %d",
            admin_user["user_id"],
            "banned" if banned else "unbanned",
            user_id,
        )
        return {
            "code": 0,
            "message": "success",
            "data": {
                "user_id": user_id,
                "is_active": user.is_active,
            },
        }


@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    request: Request,
    admin_user: dict = Depends(get_admin_user),
) -> dict[str, Any]:
    """修改用户角色 (admin only).

    Body: {"role": "admin"/"user"}
    """
    db: Database = request.app.state.db
    async with db.get_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=404, detail="用户不存在")

        body = await request.json()
        new_role = str(body.get("role", "user")).strip()
        if new_role not in ("user", "admin"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="角色必须是 user 或 admin",
            )

        user.role = new_role
        await session.commit()
        logger.info(
            "Admin %d changed user %d role to %s",
            admin_user["user_id"],
            user_id,
            new_role,
        )
        return {
            "code": 0,
            "message": "success",
            "data": {
                "user_id": user_id,
                "role": new_role,
            },
        }


@router.post("/trigger-crawl")
async def trigger_crawl(
    request: Request,
    admin_user: dict = Depends(get_admin_user),
    language: str = Query("", description="语言过滤"),
    since: str = Query("weekly", description="时间范围"),
    source: str = Query("github", description="数据源"),
) -> dict[str, Any]:
    """手动触发爬虫 (admin only)."""
    from fastapi import BackgroundTasks

    db: Database = request.app.state.db

    async def _admin_crawl() -> None:
        try:
            from devpulse.services.crawler import CrawlerService
            from devpulse.services.llm.factory import create_llm_provider
            from devpulse.services.pipeline import Pipeline
            from devpulse.services.storage import StorageService
            from devpulse.services.summarizer import Summarizer

            provider = create_llm_provider()
            crawler = CrawlerService()
            summarizer = Summarizer(provider)
            storage = StorageService(
                request.app.state.db, crawler, summarizer
            )
            pipeline = Pipeline(crawler, storage)
            result = await pipeline.run_weekly_report(
                language=language, since=since
            )
            logger.info(
                "Admin crawl completed: %s",
                result,
            )
            await provider.close()
        except Exception:
            logger.exception("Admin crawl failed")

    import asyncio
    asyncio.create_task(_admin_crawl())

    return {
        "code": 0,
        "message": "Crawl task started",
        "data": {
            "language": language,
            "since": since,
            "source": source,
        },
    }
