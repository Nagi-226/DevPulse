"""REST API 端点 — 仓库、收藏、统计与周报（JWT 认证增强）."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request

from devpulse.api.dependencies import get_current_user, get_optional_user
from devpulse.core.database import Database
from devpulse.core.repository import RepositoryDAO, WeeklyReportDAO

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/repos", tags=["repositories"])


def _repo_to_dict(r: Any) -> dict[str, Any]:
    """将 Repository ORM 对象转换为 API 响应字典."""
    return {
        "id": r.id,
        "full_name": r.full_name,
        "owner": r.owner,
        "name": r.name,
        "description": r.description,
        "language": r.language,
        "topics": r.topics,
        "total_stars": r.total_stars,
        "stars_since": r.stars_since,
        "forks": r.forks,
        "forks_since": r.forks_since,
        "open_issues": r.open_issues,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        "url": r.url,
        "has_readme": r.has_readme,
        "readme_summary": r.readme_summary,
        "key_points": r.key_points,
        "tags": r.tags,
        "summarized_at": r.summarized_at.isoformat() if r.summarized_at else None,
        "trending_rank": r.trending_rank,
        "trending_since": r.trending_since,
        "source": getattr(r, "source", "github"),
        "confidence_score": getattr(r, "confidence_score", None),
        "review_status": getattr(r, "review_status", "pending"),
        "review_required": getattr(r, "review_required", False),
    }


def _repo_to_trending_dict(r: Any) -> dict[str, Any]:
    """将 Repository ORM 对象转换为 Trending 列表响应字典."""
    return {
        "id": r.id,
        "full_name": r.full_name,
        "owner": r.owner,
        "name": r.name,
        "description": r.description,
        "language": r.language,
        "total_stars": r.total_stars,
        "stars_since": r.stars_since,
        "forks": r.forks,
        "forks_since": r.forks_since,
        "open_issues": r.open_issues,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        "topics": r.topics,
        "trending_rank": r.trending_rank,
        "source": getattr(r, "source", "github"),
        "summary": r.readme_summary,
        "key_points": r.key_points,
        "tags": r.tags,
    }


@router.get("/")
async def list_repos(
    request: Request,
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(25, ge=1, le=100, description="每页数量"),
    language: str = Query("", description="语言过滤"),
    q: str = Query("", description="搜索关键词（按名称/描述/标签 LIKE 匹配）"),
) -> dict[str, Any]:
    """列出仓库，支持分页、语言过滤和关键词搜索."""
    db: Database = request.app.state.db
    async with db.get_session() as session:
        from sqlalchemy import func, or_, select

        from devpulse.core.models import Repository

        stmt = select(Repository).order_by(Repository.total_stars.desc())

        if q:
            like_pattern = f"%{q}%"
            stmt = stmt.where(
                or_(
                    Repository.full_name.like(like_pattern),
                    Repository.description.like(like_pattern),
                    Repository.tags.like(like_pattern),
                )
            )

        if language:
            stmt = stmt.where(Repository.language == language)

        count_stmt = select(func.count()).select_from(Repository)
        if q:
            count_stmt = count_stmt.where(
                or_(
                    Repository.full_name.like(f"%{q}%"),
                    Repository.description.like(f"%{q}%"),
                    Repository.tags.like(f"%{q}%"),
                )
            )
        if language:
            count_stmt = count_stmt.where(Repository.language == language)
        total_result = await session.execute(count_stmt)
        total = total_result.scalar() or 0

        offset = (page - 1) * limit
        stmt = stmt.offset(offset).limit(limit)
        result = await session.execute(stmt)
        repos = result.scalars().all()

        return {
            "total": total,
            "page": page,
            "limit": limit,
            "items": [_repo_to_trending_dict(r) for r in repos],
        }


@router.get("/trending")
async def get_trending(
    request: Request,
    since: str = Query("weekly", description="时间范围 daily/weekly/monthly"),
    language: str = Query("", description="语言过滤"),
    source: str = Query("github", description="数据源 github/gitlab/gitee"),
    limit: int = Query(25, ge=1, le=100, description="返回条数"),
) -> dict[str, Any]:
    """获取 trending 列表（含完整字段 + 数据源过滤）."""
    db: Database = request.app.state.db
    async with db.get_session() as session:
        from sqlalchemy import select

        from devpulse.core.models import Repository

        stmt = select(Repository).order_by(Repository.trending_rank.asc().nullslast())

        if since:
            stmt = stmt.where(Repository.trending_since == since)
        if language:
            stmt = stmt.where(Repository.language == language)
        if source and source != "github":
            # 仅在显式指定非 github 时过滤（github 是默认值）
            stmt = stmt.where(Repository.source == source)
        elif source == "github":
            # github 包含 source 为 github 或 NULL（历史数据）
            from sqlalchemy import or_ as sa_or
            stmt = stmt.where(
                sa_or(Repository.source == "github", Repository.source.is_(None))
            )

        stmt = stmt.limit(limit)
        result = await session.execute(stmt)
        repos = result.scalars().all()

        return {
            "total": len(repos),
            "since": since,
            "source": source,
            "items": [_repo_to_trending_dict(r) for r in repos],
        }


# ═══════════════════════════════════════════════════════════
# 收藏端点 — 关联 JWT 用户
# ═══════════════════════════════════════════════════════════

@router.get("/collections")
async def get_collections(
    request: Request,
    current_user: dict = Depends(get_current_user),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(25, ge=1, le=100, description="每页数量"),
) -> dict[str, Any]:
    """获取当前用户的收藏列表（需登录）."""
    db: Database = request.app.state.db
    user_id = current_user["user_id"]

    async with db.get_session() as session:
        from sqlalchemy import func, select

        from devpulse.core.models import Favorite, Repository

        count_result = await session.execute(
            select(func.count()).select_from(Favorite).where(
                Favorite.user_id == user_id
            )
        )
        total = count_result.scalar() or 0

        offset = (page - 1) * page_size
        stmt = (
            select(Favorite, Repository)
            .join(Repository, Favorite.repo_id == Repository.id, isouter=True)
            .where(Favorite.user_id == user_id)
            .order_by(Favorite.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await session.execute(stmt)
        rows = result.all()

        items = []
        for fav, repo in rows:
            full_name = repo.full_name if repo else ""
            parts = full_name.split("/") if full_name else []
            items.append({
                "id": fav.id,
                "repo_id": fav.repo_id,
                "full_name": full_name,
                "owner": parts[0] if len(parts) >= 1 else "",
                "name": parts[1] if len(parts) >= 2 else "",
                "description": repo.description if repo else None,
                "language": repo.language if repo else None,
                "total_stars": repo.total_stars if repo else 0,
                "stars_since": repo.stars_since if repo else 0,
                "tags": repo.tags if repo and repo.tags else [],
                "created_at": fav.created_at.isoformat() if fav.created_at else None,
            })

        return {"total": total, "page": page, "page_size": page_size, "items": items}


@router.get("/stats/languages")
async def get_language_stats(
    request: Request,
) -> dict[str, Any]:
    """获取编程语言分布统计."""
    db: Database = request.app.state.db
    async with db.get_session() as session:
        from sqlalchemy import func, select

        from devpulse.core.models import Repository

        stmt = (
            select(Repository.language, func.count().label("count"))
            .group_by(Repository.language)
            .order_by(func.count().desc())
        )
        result = await session.execute(stmt)
        rows = result.all()

        total_count = sum(row.count for row in rows) or 1

        items = [
            {
                "language": row.language or "Other",
                "count": row.count,
                "percentage": round(row.count / total_count * 100, 1),
            }
            for row in rows
        ]

        return {"total": len(items), "items": items}


# ═══════════════════════════════════════════════════════════
# 周报端点
# ═══════════════════════════════════════════════════════════

@router.get("/weekly-reports")
async def list_weekly_reports(
    request: Request,
    limit: int = Query(10, ge=1, le=50, description="返回条数"),
    published_only: bool = Query(False, description="仅已发布"),
) -> dict[str, Any]:
    """列出周报."""
    db: Database = request.app.state.db
    async with db.get_session() as session:
        dao = WeeklyReportDAO(session)
        reports = await dao.list_reports(limit=limit, published_only=published_only)

        return {
            "total": len(reports),
            "items": [
                {
                    "id": r.id,
                    "week_start": r.week_start.isoformat(),
                    "week_end": r.week_end.isoformat(),
                    "language_filter": r.language_filter,
                    "total_repos": r.total_repos,
                    "generated_at": r.generated_at.isoformat() if r.generated_at else None,
                    "published": r.published,
                    "published_at": r.published_at.isoformat() if r.published_at else None,
                }
                for r in reports
            ],
        }


@router.get("/weekly-reports/{report_id}")
async def get_weekly_report_detail(
    report_id: int,
    request: Request,
    format: str = Query("json", description="输出格式 json/html"),
) -> Any:
    """获取周报详情（JSON 或 HTML）."""
    db: Database = request.app.state.db

    if format == "html":
        storage = request.app.state.storage_service
        html = await storage.get_weekly_report_html(report_id)
        from fastapi.responses import HTMLResponse

        return HTMLResponse(content=html)

    async with db.get_session() as session:
        from sqlalchemy import select

        from devpulse.core.models import WeeklyReport

        result = await session.execute(
            select(WeeklyReport).where(WeeklyReport.id == report_id)
        )
        report = result.scalar_one_or_none()

        if report is None:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")

        return {
            "id": report.id,
            "week_start": report.week_start.isoformat(),
            "week_end": report.week_end.isoformat(),
            "language_filter": report.language_filter,
            "total_repos": report.total_repos,
            "top_repos": report.top_repos,
            "overview_text": report.overview_text,
            "generated_at": report.generated_at.isoformat() if report.generated_at else None,
            "published": report.published,
            "published_at": report.published_at.isoformat() if report.published_at else None,
        }


# ═══════════════════════════════════════════════════════════
# 仓库详情 + 收藏操作（JWT 关联）
# ═══════════════════════════════════════════════════════════

@router.get("/{full_name:path}/star-history")
async def get_star_history(
    full_name: str,
    request: Request,
    period: str = Query("30d", description="统计周期 7d/30d/90d"),
) -> dict[str, Any]:
    """获取仓库 Star 历史趋势数据."""
    db: Database = request.app.state.db
    async with db.get_session() as session:
        from datetime import datetime as dt
        from datetime import timedelta

        from sqlalchemy import select

        from devpulse.core.models import Repository, StarHistory

        repo_result = await session.execute(
            select(Repository).where(Repository.full_name == full_name)
        )
        repo = repo_result.scalar_one_or_none()

        if repo is None:
            raise HTTPException(status_code=404, detail=f"Repository '{full_name}' not found")

        if period == "7d":
            delta = timedelta(days=7)
        elif period == "90d":
            delta = timedelta(days=90)
        else:
            delta = timedelta(days=30)

        since_date = dt.now(timezone.utc) - delta

        stmt = (
            select(StarHistory)
            .where(
                StarHistory.repo_id == repo.id,
                StarHistory.recorded_at >= since_date,
            )
            .order_by(StarHistory.recorded_at.asc())
        )
        result = await session.execute(stmt)
        history_rows = result.scalars().all()

        history = [
            {
                "date": row.recorded_at.strftime("%Y-%m-%d"),
                "stars": row.total_stars,
            }
            for row in history_rows
        ]

        return {
            "items": [
                {
                    "full_name": full_name,
                    "history": history,
                }
            ],
        }


@router.get("/{full_name:path}")
async def get_repo_detail(
    full_name: str,
    request: Request,
    current_user: dict | None = Depends(get_optional_user),
) -> dict[str, Any]:
    """获取单个仓库详情（含收藏状态）."""
    db: Database = request.app.state.db
    async with db.get_session() as session:
        dao = RepositoryDAO(session)
        repo = await dao.get_by_full_name(full_name)

        if repo is None:
            raise HTTPException(status_code=404, detail=f"Repository '{full_name}' not found")

        # 检查当前用户是否已收藏
        is_favorited = False
        if current_user:
            try:
                from sqlalchemy import select

                from devpulse.core.models import Favorite

                fav_result = await session.execute(
                    select(Favorite).where(
                        Favorite.repo_id == repo.id,
                        Favorite.user_id == current_user["user_id"],
                    )
                )
                is_favorited = fav_result.scalar_one_or_none() is not None
            except Exception:
                pass

        data = _repo_to_dict(repo)
        data["is_favorited"] = is_favorited
        return data


@router.post("/{full_name:path}/star")
async def star_repo(
    full_name: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    """收藏一个仓库（需登录）."""
    db: Database = request.app.state.db
    user_id = current_user["user_id"]

    async with db.get_session() as session:
        from sqlalchemy import select

        from devpulse.core.models import Favorite, Repository

        repo_result = await session.execute(
            select(Repository).where(Repository.full_name == full_name)
        )
        repo = repo_result.scalar_one_or_none()

        if repo is None:
            raise HTTPException(status_code=404, detail=f"Repository '{full_name}' not found")

        existing = await session.execute(
            select(Favorite).where(
                Favorite.repo_id == repo.id,
                Favorite.user_id == user_id,
            )
        )
        if existing.scalar_one_or_none() is not None:
            return {"message": "Already starred", "repo_id": repo.id}

        favorite = Favorite(
            repo_id=repo.id,  # type: ignore[arg-type]
            user_id=user_id,  # type: ignore[arg-type]
            created_at=datetime.now(timezone.utc),
        )
        session.add(favorite)
        await session.commit()
        await session.refresh(favorite)

        logger.info("User %d starred repo: %s (favorite_id=%d)", user_id, full_name, favorite.id)
        return {"message": "Starred successfully", "repo_id": repo.id}  # type: ignore[return-value]


@router.delete("/{full_name:path}/star")
async def unstar_repo(
    full_name: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> dict[str, str]:
    """取消收藏一个仓库（需登录）."""
    db: Database = request.app.state.db
    user_id = current_user["user_id"]

    async with db.get_session() as session:
        from sqlalchemy import delete, select

        from devpulse.core.models import Favorite, Repository

        repo_result = await session.execute(
            select(Repository).where(Repository.full_name == full_name)
        )
        repo = repo_result.scalar_one_or_none()
        if repo is None:
            raise HTTPException(status_code=404, detail=f"Repository '{full_name}' not found")

        fav_result = await session.execute(
            select(Favorite).where(
                Favorite.repo_id == repo.id,
                Favorite.user_id == user_id,
            )
        )
        favorite = fav_result.scalar_one_or_none()

        if favorite is None:
            raise HTTPException(status_code=404, detail=f"Favorite for '{full_name}' not found")

        await session.execute(
            delete(Favorite).where(Favorite.id == favorite.id)
        )
        await session.commit()

        logger.info("User %d unstarred repo: %s", user_id, full_name)
        return {"message": "Unstarred successfully"}


@router.post("/crawl")
async def crawl_trending(
    request: Request,
    background_tasks: BackgroundTasks,
    language: str = Query("", description="语言过滤"),
    since: str = Query("weekly", description="时间范围"),
    source: str = Query("github", description="数据源 github/gitlab/gitee"),
    limit: int = Query(25, ge=1, le=50, description="返回条数"),
) -> dict[str, Any]:
    """触发爬虫（后台异步任务），含链式 LLM 摘要."""

    async def _crawl() -> None:
        try:
            from devpulse.services.storage import StorageService

            storage: StorageService = request.app.state.storage_service
            result = await storage.crawl_and_store_trending(
                language=language, since=since, limit=limit
            )
            logger.info(
                "Background crawl completed: stored=%d, summarized=%d",
                result.get("stored", 0),
                result.get("summarized", 0),
            )
        except Exception:
            logger.exception("Background crawl failed")

    background_tasks.add_task(_crawl)
    return {
        "message": "Crawl task started",
        "language": language,
        "since": since,
        "source": source,
    }


@router.post("/{full_name:path}/summarize")
async def summarize_repo(
    full_name: str,
    request: Request,
    background_tasks: BackgroundTasks,
) -> dict[str, str]:
    """触发单个仓库摘要生成（后台异步任务）."""
    db: Database = request.app.state.db

    async def _summarize() -> None:
        try:
            storage = request.app.state.storage_service
            async with db.get_session() as session:
                dao = RepositoryDAO(session)
                repo = await dao.get_by_full_name(full_name)
                if repo is None:
                    logger.warning("Repo not found for summarize: %s", full_name)
                    return
                repo_id = repo.id  # type: ignore[assignment]
            await storage.summarize_and_update(
                repo_ids=[repo_id],
                only_without_summary=False,
            )
            logger.info("Background summarize completed for %s", full_name)
        except Exception:
            logger.exception("Background summarize failed for %s", full_name)

    background_tasks.add_task(_summarize)
    return {"message": "Summarize task started", "full_name": full_name}
