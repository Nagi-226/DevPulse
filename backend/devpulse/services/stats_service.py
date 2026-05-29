"""每日统计数据服务 — DAU/阅读量/收藏/LLM 成本追踪."""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import func, select

from devpulse.core.models import DailyStats, Favorite, Repository, User

logger = logging.getLogger(__name__)


class StatsService:
    """每日运营数据统计服务.

    职责:
        - 记录每日 DAU/页面浏览/新用户/爬虫次数/LLM 成本
        - 聚合 Dashboard 看板数据
    """

    @staticmethod
    async def record_daily_stats(
        session: Any,
        dau: int = 0,
        page_views: int = 0,
        new_users: int = 0,
        crawl_count: int = 0,
        llm_cost: float = 0.0,
    ) -> DailyStats:
        """记录当天统计数据 (upsert).

        同一天多次调用会累加 page_views、crawl_count、llm_cost，
        并更新 dau 和 new_users 为最新值.

        Args:
            session: SQLAlchemy 异步 session.
            dau: 当日活跃用户数.
            page_views: 页面浏览量.
            new_users: 新注册用户数.
            crawl_count: 爬虫执行次数.
            llm_cost: LLM API 费用 (USD).

        Returns:
            保存后的 DailyStats 对象.
        """
        today = date.today()

        result = await session.execute(
            select(DailyStats).where(DailyStats.date == today)
        )
        stats = result.scalar_one_or_none()

        if stats is None:
            stats = DailyStats(
                date=today,
                dau=dau,
                page_views=page_views,
                new_users=new_users,
                crawl_count=crawl_count,
                llm_cost=llm_cost,
                created_at=datetime.now(timezone.utc),
            )
            session.add(stats)
        else:
            stats.dau = max(stats.dau, dau)
            stats.page_views += page_views
            stats.new_users = max(stats.new_users, new_users)
            stats.crawl_count += crawl_count
            stats.llm_cost += llm_cost

        await session.commit()
        await session.refresh(stats)
        return stats

    @staticmethod
    async def get_dashboard_data(session: Any, days: int = 30) -> dict[str, Any]:
        """获取管理后台 Dashboard 聚合数据.

        Args:
            session: SQLAlchemy 异步 session.
            days: 统计最近 N 天数据，默认 30.

        Returns:
            {
                summary: {dau, page_views, favorites_count, llm_cost},
                daily_trend: [{date, dau, page_views, llm_cost}],
                total_users: int,
                total_repos: int,
            }
        """
        # ── 汇总统计 ────────────────────────────
        trend_result = await session.execute(
            select(DailyStats)
            .order_by(DailyStats.date.desc())
            .limit(days)
        )
        trend_rows = trend_result.scalars().all()

        total_dau = max((r.dau for r in trend_rows), default=0)
        total_page_views = sum(r.page_views for r in trend_rows)
        total_llm_cost = round(sum(r.llm_cost for r in trend_rows), 4)

        # ── 收藏总数 ────────────────────────────
        fav_result = await session.execute(
            select(func.count()).select_from(Favorite)
        )
        favorites_count = fav_result.scalar() or 0

        # ── 用户总数 ────────────────────────────
        user_result = await session.execute(
            select(func.count()).select_from(User)
        )
        total_users = user_result.scalar() or 0

        # ── 仓库总数 ────────────────────────────
        repo_result = await session.execute(
            select(func.count()).select_from(Repository)
        )
        total_repos = repo_result.scalar() or 0

        # ── 每日趋势 ────────────────────────────
        daily_trend = [
            {
                "date": r.date.isoformat() if isinstance(r.date, date) else str(r.date),
                "dau": r.dau,
                "page_views": r.page_views,
                "new_users": r.new_users,
                "crawl_count": r.crawl_count,
                "llm_cost": round(r.llm_cost, 4),
            }
            for r in reversed(trend_rows)  # 从旧到新
        ]

        return {
            "summary": {
                "dau": total_dau,
                "page_views": total_page_views,
                "favorites_count": favorites_count,
                "llm_cost": total_llm_cost,
            },
            "daily_trend": daily_trend,
            "total_users": total_users,
            "total_repos": total_repos,
        }

    @staticmethod
    async def record_llm_cost(session: Any, cost: float) -> None:
        """便捷方法：追加 LLM 成本到当天统计.

        Args:
            session: SQLAlchemy 异步 session.
            cost: 本次 LLM 调用费用 (USD).
        """
        if cost <= 0:
            return
        await StatsService.record_daily_stats(
            session=session,
            llm_cost=cost,
        )
