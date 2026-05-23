"""数据访问层 — Repository Pattern 实现."""

from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from devpulse.core.models import Repository, WeeklyReport

logger = logging.getLogger(__name__)


class RepositoryDAO:
    """Repository 表的数据访问对象."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_or_update(self, repo_data: dict) -> Repository:
        """存在则更新，不存在则创建.

        Args:
            repo_data: 仓库数据字典，必须包含 ``full_name``.

        Returns:
            已持久化的 Repository 对象.
        """
        stmt = (
            sqlite_insert(Repository)
            .values(**repo_data)
            .on_conflict_do_update(
                index_elements=["full_name"],
                set_={
                    k: v for k, v in repo_data.items() if k != "full_name"
                },
            )
        )
        await self._session.execute(stmt)
        await self._session.commit()

        # 重新查询返回完整对象（populate_existing 确保绕过 identity map）
        result = await self._session.execute(
            select(Repository)
            .where(Repository.full_name == repo_data["full_name"])
            .execution_options(populate_existing=True)
        )
        return result.scalar_one()

    async def bulk_create_or_update(self, repos_data: list[dict]) -> list[Repository]:
        """批量 upsert 仓库数据.

        Args:
            repos_data: 仓库数据字典列表.

        Returns:
            已持久化的 Repository 对象列表.
        """
        if not repos_data:
            return []

        results: list[Repository] = []
        for repo_data in repos_data:
            repo = await self.create_or_update(repo_data)
            results.append(repo)

        logger.info("Bulk upsert completed: %d repos", len(results))
        return results

    async def get_by_full_name(self, full_name: str) -> Repository | None:
        """按完整仓库名查询.

        Args:
            full_name: 仓库完整名，如 ``microsoft/codegraph``.

        Returns:
            Repository 对象或 None.
        """
        result = await self._session.execute(
            select(Repository).where(Repository.full_name == full_name)
        )
        return result.scalar_one_or_none()

    async def get_trending_repos(
        self,
        since: str = "weekly",
        limit: int = 25,
    ) -> list[Repository]:
        """按 trending_rank 排序获取 trending 列表.

        Args:
            since: 时间范围 weekly/daily/monthly.
            limit: 返回条数上限.

        Returns:
            Repository 对象列表.
        """
        result = await self._session.execute(
            select(Repository)
            .where(
                Repository.trending_since == since,
                Repository.trending_rank.isnot(None),
            )
            .order_by(Repository.trending_rank)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_repos_by_language(
        self,
        language: str,
        limit: int = 50,
    ) -> list[Repository]:
        """按编程语言筛选仓库.

        Args:
            language: 编程语言名称.
            limit: 返回条数上限.

        Returns:
            Repository 对象列表.
        """
        result = await self._session.execute(
            select(Repository)
            .where(Repository.language == language)
            .order_by(Repository.total_stars.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_repos_without_summary(self, limit: int = 10) -> list[Repository]:
        """获取尚未生成摘要的仓库.

        Args:
            limit: 返回条数上限.

        Returns:
            Repository 对象列表.
        """
        result = await self._session.execute(
            select(Repository)
            .where(Repository.readme_summary.is_(None))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_summary(
        self,
        repo_id: int,
        summary: str,
        key_points: list[str],
        tags: list[str],
    ) -> None:
        """更新仓库的摘要信息.

        Args:
            repo_id: 仓库 ID.
            summary: LLM 生成的摘要文本.
            key_points: 关键要点列表.
            tags: 标签列表.
        """
        await self._session.execute(
            update(Repository)
            .where(Repository.id == repo_id)
            .values(
                readme_summary=summary,
                key_points=key_points,
                tags=tags,
                summarized_at=datetime.now(),
            )
        )
        await self._session.commit()
        logger.info("Summary updated for repo_id=%d", repo_id)

    async def delete_by_full_name(self, full_name: str) -> bool:
        """按完整仓库名删除记录.

        Args:
            full_name: 仓库完整名.

        Returns:
            是否成功删除.
        """
        repo = await self.get_by_full_name(full_name)
        if repo is None:
            return False
        await self._session.delete(repo)
        await self._session.commit()
        logger.info("Deleted repo: %s", full_name)
        return True


class WeeklyReportDAO:
    """WeeklyReport 表的数据访问对象."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_weekly_report(
        self,
        week_start: datetime,
        week_end: datetime,
        language_filter: str | None,
        total_repos: int,
        top_repos: list[int],
        overview_text: str,
    ) -> WeeklyReport:
        """创建一条周报记录.

        Args:
            week_start: 周起始日期.
            week_end: 周结束日期.
            language_filter: 语言过滤，None 表示全语言.
            total_repos: 本周项目总数.
            top_repos: Top 项目 ID 列表.
            overview_text: LLM 生成周报导语.

        Returns:
            新创建的 WeeklyReport 对象.
        """
        report = WeeklyReport(
            week_start=week_start,
            week_end=week_end,
            language_filter=language_filter,
            total_repos=total_repos,
            top_repos=top_repos,
            overview_text=overview_text,
            generated_at=datetime.now(),
        )
        self._session.add(report)
        await self._session.commit()
        await self._session.refresh(report)
        return report

    async def get_weekly_report(self, week_start: datetime) -> WeeklyReport | None:
        """按周起始日查询周报.

        Args:
            week_start: 周起始日期.

        Returns:
            WeeklyReport 对象或 None.
        """
        result = await self._session.execute(
            select(WeeklyReport).where(WeeklyReport.week_start == week_start)
        )
        return result.scalar_one_or_none()

    async def list_reports(
        self,
        limit: int = 10,
        published_only: bool = False,
    ) -> list[WeeklyReport]:
        """列出周报列表.

        Args:
            limit: 返回条数上限.
            published_only: 是否仅返回已发布的.

        Returns:
            WeeklyReport 对象列表.
        """
        stmt = select(WeeklyReport).order_by(WeeklyReport.week_start.desc()).limit(limit)
        if published_only:
            stmt = stmt.where(WeeklyReport.published.is_(True))

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def mark_published(self, report_id: int) -> None:
        """将周报标记为已发布.

        Args:
            report_id: 周报 ID.
        """
        await self._session.execute(
            update(WeeklyReport)
            .where(WeeklyReport.id == report_id)
            .values(published=True, published_at=datetime.now())
        )
        await self._session.commit()
        logger.info("Weekly report %d marked as published", report_id)
