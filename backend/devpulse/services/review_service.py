"""内容审核服务 — 待审核项目管理与审批."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select, update

from devpulse.core.models import Repository

logger = logging.getLogger(__name__)


class ReviewService:
    """管理 LLM 摘要审核流程.

    职责:
        - 查询待审核项目 (review_status = 'pending')
        - 审批通过 / 拒绝
        - 统计审核状态
    """

    @staticmethod
    async def get_pending_reviews(
        session: Any,
        page: int = 1,
        page_size: int = 25,
    ) -> dict[str, Any]:
        """获取待审核项目列表 (review_status='pending').

        Args:
            session: SQLAlchemy 异步 session.
            page: 页码.
            page_size: 每页数量.

        Returns:
            {total, page, page_size, items}.
        """
        # 总数
        count_stmt = (
            select(func.count())
            .select_from(Repository)
            .where(Repository.review_status == "pending")
        )
        total_result = await session.execute(count_stmt)
        total = total_result.scalar() or 0

        # 分页查询
        offset = (page - 1) * page_size
        stmt = (
            select(Repository)
            .where(Repository.review_status == "pending")
            .order_by(Repository.confidence_score.asc().nullsfirst())
            .offset(offset)
            .limit(page_size)
        )
        result = await session.execute(stmt)
        repos = result.scalars().all()

        items = [
            {
                "id": r.id,
                "full_name": r.full_name,
                "owner": r.owner,
                "name": r.name,
                "description": r.description,
                "language": r.language,
                "readme_summary": r.readme_summary,
                "key_points": r.key_points,
                "confidence_score": r.confidence_score,
                "review_status": r.review_status,
                "crawled_at": r.crawled_at.isoformat() if r.crawled_at else None,
                "summarized_at": r.summarized_at.isoformat() if r.summarized_at else None,
            }
            for r in repos
        ]

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": items,
        }

    @staticmethod
    async def approve_review(session: Any, repo_id: int) -> dict[str, Any]:
        """审核通过一个项目.

        Args:
            session: SQLAlchemy 异步 session.
            repo_id: 仓库 ID.

        Returns:
            {repo_id, review_status, message}.

        Raises:
            ValueError: 仓库不存在.
        """
        result = await session.execute(
            select(Repository).where(Repository.id == repo_id)
        )
        repo = result.scalar_one_or_none()
        if repo is None:
            raise ValueError(f"Repository id={repo_id} not found")

        repo.review_status = "approved"
        await session.commit()

        logger.info("Review approved: repo_id=%d full_name=%s", repo_id, repo.full_name)
        return {
            "repo_id": repo_id,
            "review_status": "approved",
            "message": f"Review approved for {repo.full_name}",
        }

    @staticmethod
    async def reject_review(session: Any, repo_id: int) -> dict[str, Any]:
        """审核拒绝一个项目.

        Args:
            session: SQLAlchemy 异步 session.
            repo_id: 仓库 ID.

        Returns:
            {repo_id, review_status, message}.

        Raises:
            ValueError: 仓库不存在.
        """
        result = await session.execute(
            select(Repository).where(Repository.id == repo_id)
        )
        repo = result.scalar_one_or_none()
        if repo is None:
            raise ValueError(f"Repository id={repo_id} not found")

        repo.review_status = "rejected"
        await session.commit()

        logger.info("Review rejected: repo_id=%d full_name=%s", repo_id, repo.full_name)
        return {
            "repo_id": repo_id,
            "review_status": "rejected",
            "message": f"Review rejected for {repo.full_name}",
        }

    @staticmethod
    async def get_review_stats(session: Any) -> dict[str, int]:
        """获取审核状态统计.

        Args:
            session: SQLAlchemy 异步 session.

        Returns:
            {total, pending, approved, rejected}.
        """
        stmt = (
            select(
                Repository.review_status,
                func.count().label("count"),
            )
            .group_by(Repository.review_status)
        )
        result = await session.execute(stmt)
        rows = result.all()

        stats: dict[str, int] = {"total": 0, "pending": 0, "approved": 0, "rejected": 0}
        for status, count in rows:
            key = status or "pending"
            if key in stats:
                stats[key] = count
            stats["total"] += count

        return stats
