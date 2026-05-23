"""存储服务编排 — 整合爬虫、摘要、存储的完整流水线."""

from __future__ import annotations

import logging
from datetime import datetime

from devpulse.core.database import Database
from devpulse.core.repository import RepositoryDAO, WeeklyReportDAO
from devpulse.services.crawler import CrawlerService
from devpulse.services.summarizer import Summarizer

logger = logging.getLogger(__name__)

# 需要从字符串转为 datetime 的字段
_DATETIME_FIELDS = {"created_at", "updated_at"}


def _normalize_datetime_fields(data: dict) -> dict:
    """将字符串日期转换为 datetime 对象.

    Args:
        data: 包含可能为字符串的日期字段的字典.

    Returns:
        转换后的字典（原地修改）.
    """
    for field in _DATETIME_FIELDS:
        value = data.get(field)
        if isinstance(value, str):
            try:
                data[field] = datetime.fromisoformat(value)
            except ValueError:
                logger.debug(
                    "Cannot parse date field '%s', setting to None", field
                )
                data[field] = None
    return data


class StorageService:
    """存储服务编排层.

    整合爬虫采集、LLM 摘要、数据持久化的完整流水线。

    Args:
        db: Database 实例.
        crawler: CrawlerService 实例.
        summarizer: Summarizer 实例.
    """

    def __init__(
        self,
        db: Database,
        crawler: CrawlerService,
        summarizer: Summarizer,
    ) -> None:
        self._db = db
        self._crawler = crawler
        self._summarizer = summarizer

    async def crawl_and_store_trending(
        self,
        language: str = "",
        since: str = "weekly",
        limit: int = 25,
    ) -> list[dict]:
        """爬取 Trending 并持久化存储.

        流程：
        1. 调用 crawler.crawl_trending_repos 获取数据
        2. 调用 repository_dao.bulk_create_or_update 存储
        3. 返回已存储的数据

        Args:
            language: 语言过滤.
            since: 时间范围.
            limit: 返回条数上限.

        Returns:
            已存储的仓库数据字典列表.
        """
        repos_data = await self._crawler.crawl_trending_repos(
            language=language, since=since, limit=limit
        )

        if not repos_data:
            logger.warning("No trending data fetched for language=%s since=%s", language, since)
            return []

        stored: list[dict] = []
        async with self._db.get_session() as session:
            dao = RepositoryDAO(session)
            for i, data in enumerate(repos_data):
                data["trending_rank"] = i + 1
                data["trending_since"] = since
                data["crawled_at"] = datetime.now()
                # 转换日期字段
                _normalize_datetime_fields(data)
                repo = await dao.create_or_update(data)
                stored.append(
                    {
                        "id": repo.id,
                        "full_name": repo.full_name,
                        "total_stars": repo.total_stars,
                        "stars_since": repo.stars_since,
                    }
                )

        logger.info("Crawled and stored %d repos", len(stored))
        return stored

    async def summarize_and_update(
        self,
        repo_ids: list[int] | None = None,
        batch_size: int = 5,
    ) -> int:
        """为指定仓库生成摘要并回写数据库.

        流程：
        1. 如果 repo_ids 为 None，则获取未摘要的项目
        2. 分批调用 summarizer.summarize_batch
        3. 调用 repository_dao.update_summary 更新摘要字段

        Args:
            repo_ids: 目标仓库 ID 列表，None 表示自动获取未摘要项目.
            batch_size: 每批处理数量.

        Returns:
            已生成摘要的仓库数量.
        """
        async with self._db.get_session() as session:
            dao = RepositoryDAO(session)

            if repo_ids is None:
                repos = await dao.get_repos_without_summary(limit=batch_size * 10)
            else:
                from sqlalchemy import select

                from devpulse.core.models import Repository as RepoModel

                result = await session.execute(
                    select(RepoModel).where(RepoModel.id.in_(repo_ids))
                )
                repos = list(result.scalars().all())

            if not repos:
                logger.info("No repos to summarize")
                return 0

            # 转换为字典格式供 summarizer 使用
            repo_dicts = [
                {
                    "full_name": r.full_name,
                    "description": r.description or "",
                    "language": r.language or "",
                    "total_stars": r.total_stars,
                    "stars_since": r.stars_since,
                    "topics": r.topics or [],
                }
                for r in repos
            ]

            total_summarized = 0
            for i in range(0, len(repo_dicts), batch_size):
                batch = repo_dicts[i : i + batch_size]
                batch_repos = repos[i : i + batch_size]

                summarized = await self._summarizer.summarize_batch(batch)

                for repo_obj, result in zip(batch_repos, summarized, strict=False):
                    await dao.update_summary(
                        repo_id=repo_obj.id,  # type: ignore[arg-type]
                        summary=result.get("summary", ""),
                        key_points=result.get("key_points", []),
                        tags=result.get("tags", []),
                    )
                    total_summarized += 1

        logger.info("Summarized %d repos", total_summarized)
        return total_summarized

    async def generate_weekly_report(
        self,
        week_start: datetime,
        language_filter: str | None = None,
    ) -> dict:
        """生成周报.

        流程：
        1. 获取本周 trending 数据
        2. 调用 summarizer.generate_weekly_overview 生成导语
        3. 创建 WeeklyReport 记录

        Args:
            week_start: 周起始日期.
            language_filter: 语言过滤.

        Returns:
            周报摘要字典.
        """
        from datetime import timedelta

        week_end = week_start + timedelta(days=7)

        async with self._db.get_session() as session:
            repo_dao = RepositoryDAO(session)
            report_dao = WeeklyReportDAO(session)

            trending = await repo_dao.get_trending_repos(since="weekly", limit=25)

            top_repos = [r.id for r in trending[:10]]  # type: ignore[misc]

            # 生成导语
            overview_text = ""
            if trending:
                overview_dicts = [
                    {
                        "full_name": r.full_name,
                        "summary": r.readme_summary or "",
                    }
                    for r in trending
                ]
                overview_text = await self._summarizer.generate_weekly_overview(
                    overview_dicts
                )

            report = await report_dao.create_weekly_report(
                week_start=week_start,
                week_end=week_end,
                language_filter=language_filter,
                total_repos=len(trending),
                top_repos=top_repos,
                overview_text=overview_text,
            )

            return {
                "id": report.id,
                "week_start": report.week_start,
                "week_end": report.week_end,
                "total_repos": report.total_repos,
                "overview_text": report.overview_text,
            }

    async def get_weekly_report_html(self, report_id: int) -> str:
        """生成 HTML 格式周报.

        Args:
            report_id: 周报 ID.

        Returns:
            HTML 字符串.
        """
        async with self._db.get_session() as session:
            from sqlalchemy import select as sa_select

            from devpulse.core.models import Repository as RepoModel
            from devpulse.core.models import WeeklyReport as WrModel

            result = await session.execute(
                sa_select(WrModel).where(WrModel.id == report_id)
            )
            report = result.scalar_one_or_none()

            if report is None:
                return "<html><body><h1>Report Not Found</h1></body></html>"

            # 获取 Top Repos 详情
            repo_list_html = ""
            if report.top_repos:
                repos_result = await session.execute(
                    sa_select(RepoModel).where(RepoModel.id.in_(report.top_repos))
                )
                repos = repos_result.scalars().all()
                for repo in repos:
                    repo_list_html += f"""
                    <li>
                        <strong>{repo.full_name}</strong> ({repo.language or 'N/A'})
                        - {repo.total_stars} stars
                        <p>{repo.readme_summary or ''}</p>
                    </li>"""

            return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>DevPulse 周报 {report.week_start.date()}</title>
    <style>
        body {{
            font-family: system-ui, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
        }}
        h1 {{ color: #333; }}
        .overview {{ background: #f5f5f5; padding: 1rem; border-radius: 8px; margin: 1rem 0; }}
        ul {{ list-style: none; padding: 0; }}
        li {{ border-bottom: 1px solid #eee; padding: 1rem 0; }}
    </style>
</head>
<body>
    <h1>DevPulse 周报 — {report.week_start.date()} ~ {report.week_end.date()}</h1>
    <p>共收录 {report.total_repos} 个项目</p>
    <div class="overview">
        <h2>本周趋势概览</h2>
        <p>{report.overview_text or '暂无摘要'}</p>
    </div>
    <h2>TOP 项目</h2>
    <ul>{repo_list_html}</ul>
</body>
</html>"""
