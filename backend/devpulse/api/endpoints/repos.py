"""REST API 端点 — 仓库与周报."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request

from devpulse.core.database import Database
from devpulse.core.repository import RepositoryDAO, WeeklyReportDAO

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/repos", tags=["repositories"])





@router.get("/")
async def list_repos(
    request: Request,
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(25, ge=1, le=100, description="每页数量"),
    language: str = Query("", description="语言过滤"),
) -> dict[str, Any]:
    """列出仓库，支持分页和语言过滤."""
    db: Database = request.app.state.db
    async with db.get_session() as session:
        from sqlalchemy import func, select

        from devpulse.core.models import Repository

        stmt = select(Repository).order_by(Repository.total_stars.desc())
        if language:
            stmt = stmt.where(Repository.language == language)

        # 总数
        count_stmt = select(func.count()).select_from(Repository)
        if language:
            count_stmt = count_stmt.where(Repository.language == language)
        total_result = await session.execute(count_stmt)
        total = total_result.scalar() or 0

        # 分页
        offset = (page - 1) * limit
        stmt = stmt.offset(offset).limit(limit)
        result = await session.execute(stmt)
        repos = result.scalars().all()

        return {
            "total": total,
            "page": page,
            "limit": limit,
            "items": [
                {
                    "id": r.id,
                    "full_name": r.full_name,
                    "owner": r.owner,
                    "name": r.name,
                    "description": r.description,
                    "language": r.language,
                    "total_stars": r.total_stars,
                    "stars_since": r.stars_since,
                    "forks": r.forks,
                    "topics": r.topics,
                    "trending_rank": r.trending_rank,
                    "trending_since": r.trending_since,
                    "summarized_at": r.summarized_at,
                }
                for r in repos
            ],
        }


@router.get("/trending")
async def get_trending(
    request: Request,
    since: str = Query("weekly", description="时间范围 daily/weekly/monthly"),
    limit: int = Query(25, ge=1, le=100, description="返回条数"),
) -> dict[str, Any]:
    """获取 trending 列表."""
    db: Database = request.app.state.db
    async with db.get_session() as session:
        dao = RepositoryDAO(session)
        repos = await dao.get_trending_repos(since=since, limit=limit)

        return {
            "total": len(repos),
            "since": since,
            "items": [
                {
                    "id": r.id,
                    "full_name": r.full_name,
                    "owner": r.owner,
                    "name": r.name,
                    "description": r.description,
                    "language": r.language,
                    "total_stars": r.total_stars,
                    "stars_since": r.stars_since,
                    "topics": r.topics,
                    "trending_rank": r.trending_rank,
                    "summary": r.readme_summary,
                    "key_points": r.key_points,
                    "tags": r.tags,
                }
                for r in repos
            ],
        }


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


@router.get("/{full_name:path}")
async def get_repo_detail(
    full_name: str,
    request: Request,
) -> dict[str, Any]:
    """获取单个仓库详情."""
    db: Database = request.app.state.db
    async with db.get_session() as session:
        dao = RepositoryDAO(session)
        repo = await dao.get_by_full_name(full_name)

        if repo is None:
            raise HTTPException(status_code=404, detail=f"Repository '{full_name}' not found")

        return {
            "id": repo.id,
            "full_name": repo.full_name,
            "owner": repo.owner,
            "name": repo.name,
            "description": repo.description,
            "language": repo.language,
            "topics": repo.topics,
            "total_stars": repo.total_stars,
            "stars_since": repo.stars_since,
            "forks": repo.forks,
            "forks_since": repo.forks_since,
            "open_issues": repo.open_issues,
            "created_at": repo.created_at.isoformat() if repo.created_at else None,
            "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
            "url": repo.url,
            "has_readme": repo.has_readme,
            "readme_summary": repo.readme_summary,
            "key_points": repo.key_points,
            "tags": repo.tags,
            "crawled_at": repo.crawled_at.isoformat() if repo.crawled_at else None,
            "summarized_at": repo.summarized_at.isoformat() if repo.summarized_at else None,
            "trending_rank": repo.trending_rank,
            "trending_since": repo.trending_since,
        }


@router.post("/crawl")
async def crawl_trending(
    request: Request,
    background_tasks: BackgroundTasks,
    language: str = Query("", description="语言过滤"),
    since: str = Query("weekly", description="时间范围"),
    limit: int = Query(25, ge=1, le=50, description="返回条数"),
) -> dict[str, str]:
    """触发爬虫（后台异步任务）."""

    async def _crawl() -> None:
        try:
            from devpulse.services.storage import StorageService

            # 此处依赖注入需在 main.py 中预配置 app.state
            storage: StorageService = request.app.state.storage_service
            await storage.crawl_and_store_trending(
                language=language, since=since, limit=limit
            )
            logger.info("Background crawl completed")
        except Exception:
            logger.exception("Background crawl failed")

    background_tasks.add_task(_crawl)
    return {"message": "Crawl task started", "language": language, "since": since}


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
            await storage.summarize_and_update(repo_ids=[repo_id])
            logger.info("Background summarize completed for %s", full_name)
        except Exception:
            logger.exception("Background summarize failed for %s", full_name)

    background_tasks.add_task(_summarize)
    return {"message": "Summarize task started", "full_name": full_name}
