"""AI 推荐引擎 — 协同过滤 + 内容过滤 + 热门降级."""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

import numpy as np
from sqlalchemy import func, select

from devpulse.core.models import Repository, UserBehavior

logger = logging.getLogger(__name__)

# 行为权重
ACTION_WEIGHTS: dict[str, float] = {
    "view": 0.5,
    "star": 1.0,
    "like": 0.8,
    "share": 1.2,
    "comment": 1.0,
}

# 冷启动阈值：至少需要 N 条行为记录才能启用协同过滤
MIN_BEHAVIORS_FOR_CF = 3


class RecommendationEngine:
    """推荐引擎（三层降级策略）.

    L1: 协同过滤 (cosine_similarity on user-repo matrix)
    L2: 内容过滤 (基于语言/主题匹配的热门项目)
    L3: 全局热门 (trending_rank ASC, total_stars DESC)
    """

    @staticmethod
    async def get_recommendations(
        session: Any,
        user_id: int | None = None,
        limit: int = 25,
    ) -> dict[str, Any]:
        """为用户生成个性化推荐.

        Args:
            session: SQLAlchemy 异步 session.
            user_id: 用户 ID，None 表示匿名用户.
            limit: 返回条数上限.

        Returns:
            {items: [...], method: str, fallback_level: int}
        """
        # 匿名用户 → 直接降级 L3
        if user_id is None:
            return await RecommendationEngine._get_popular_recommendations(
                session, limit, method="popular", fallback_level=3
            )

        # 获取用户行为
        behaviors_result = await session.execute(
            select(UserBehavior)
            .where(UserBehavior.user_id == user_id)
            .order_by(UserBehavior.created_at.desc())
        )
        behaviors = behaviors_result.scalars().all()

        # 行为不足 → L2 或 L3
        if len(behaviors) < MIN_BEHAVIORS_FOR_CF:
            # 检查是否有语言偏好
            interacted_repo_ids = list({b.repo_id for b in behaviors})
            if interacted_repo_ids:
                repos_result = await session.execute(
                    select(Repository).where(Repository.id.in_(interacted_repo_ids))
                )
                repos = repos_result.scalars().all()
                languages = list({r.language for r in repos if r.language})
                if languages:
                    return await RecommendationEngine._get_content_recommendations(
                        session, languages, limit, fallback_level=2
                    )

            return await RecommendationEngine._get_popular_recommendations(
                session, limit, method="popular", fallback_level=3
            )

        # L1: 协同过滤
        try:
            return await RecommendationEngine._get_collaborative_recommendations(
                session, user_id, behaviors, limit
            )
        except Exception:
            logger.exception("Collaborative filtering failed, falling back to L2")
            return await RecommendationEngine._get_popular_recommendations(
                session, limit, method="popular_fallback", fallback_level=3
            )

    @staticmethod
    async def _get_collaborative_recommendations(
        session: Any, user_id: int, user_behaviors: list[UserBehavior], limit: int
    ) -> dict[str, Any]:
        """L1: 协同过滤推荐."""
        # 获取全局行为数据
        all_behaviors_result = await session.execute(
            select(UserBehavior)
        )
        all_behaviors = all_behaviors_result.scalars().all()

        # 构建 user-repo 矩阵
        user_repo_weights: dict[int, dict[int, float]] = defaultdict(
            lambda: defaultdict(float)
        )
        for b in all_behaviors:
            weight = ACTION_WEIGHTS.get(b.action_type, 1.0) * b.weight
            user_repo_weights[b.user_id][b.repo_id] += weight

        user_ids = list(user_repo_weights.keys())
        if len(user_ids) < 2:
            return await RecommendationEngine._get_popular_recommendations(
                session, limit, method="popular_cf_insufficient", fallback_level=3
            )

        # 获取所有被交互过的 repo IDs
        all_repo_ids = set()
        for repo_map in user_repo_weights.values():
            all_repo_ids.update(repo_map.keys())
        repo_id_list = sorted(all_repo_ids)

        # 构建稀疏矩阵
        user_idx_map = {uid: i for i, uid in enumerate(user_ids)}
        repo_idx_map = {rid: i for i, rid in enumerate(repo_id_list)}
        n_users = len(user_ids)
        n_repos = len(repo_id_list)

        matrix = np.zeros((n_users, n_repos), dtype=np.float32)
        for uid, repo_map in user_repo_weights.items():
            ui = user_idx_map[uid]
            for rid, weight in repo_map.items():
                ri = repo_idx_map[rid]
                matrix[ui, ri] = weight

        # 计算用户相似度
        from sklearn.metrics.pairwise import cosine_similarity

        user_similarity = cosine_similarity(matrix)

        # 找到目标用户的行
        if user_id not in user_idx_map:
            return await RecommendationEngine._get_popular_recommendations(
                session, limit, method="popular_nouser", fallback_level=3
            )

        target_idx = user_idx_map[user_id]

        # 获取用户已交互的 repo
        user_repos = set(b.repo_id for b in user_behaviors)

        # 加权评分: 基于相似用户的权重
        scores: dict[int, float] = defaultdict(float)
        total_sim = 0.0
        for other_idx in range(n_users):
            if other_idx == target_idx:
                continue
            sim = float(user_similarity[target_idx, other_idx])
            if sim <= 0:
                continue
            total_sim += sim
            for ri, rid in enumerate(repo_id_list):
                weight = float(matrix[other_idx, ri])
                if weight > 0 and rid not in user_repos:
                    scores[rid] += weight * sim

        # 排序取 top-N
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_repo_ids = [rid for rid, _ in sorted_scores[:limit]]

        if not top_repo_ids:
            return await RecommendationEngine._get_popular_recommendations(
                session, limit, method="popular_cf_empty", fallback_level=3
            )

        # 查询仓库详情
        repos_result = await session.execute(
            select(Repository).where(Repository.id.in_(top_repo_ids))
        )
        repos = {r.id: r for r in repos_result.scalars().all()}

        items = []
        for rid, score in sorted_scores[:limit]:
            repo = repos.get(rid)
            if repo is None:
                continue
            items.append({
                "repo": _repo_to_recommendation_dict(repo),
                "score": round(float(score), 4),
                "method": "collaborative",
                "reason": _generate_cf_reason(rid, user_behaviors),
            })

        return {"items": items, "method": "collaborative", "fallback_level": 1}

    @staticmethod
    async def _get_content_recommendations(
        session: Any,
        languages: list[str],
        limit: int,
        fallback_level: int = 2,
    ) -> dict[str, Any]:
        """L2: 基于语言/主题的内容过滤."""
        from sqlalchemy import or_

        conditions = []
        for lang in languages:
            conditions.append(Repository.language == lang)
            conditions.append(Repository.topics.contains([lang]))

        stmt = (
            select(Repository)
            .where(
                or_(*conditions),
                Repository.review_status != "rejected",
            )
            .order_by(Repository.total_stars.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        repos = result.scalars().all()

        items = [
            {
                "repo": _repo_to_recommendation_dict(r),
                "score": 0.7,
                "method": "content",
                "reason": f"基于你对 {languages[0] if languages else '开源'} 的偏好",
            }
            for r in repos
        ]

        if not items:
            return await RecommendationEngine._get_popular_recommendations(
                session, limit, method="popular", fallback_level=3
            )

        return {"items": items, "method": "content", "fallback_level": fallback_level}

    @staticmethod
    async def _get_popular_recommendations(
        session: Any,
        limit: int,
        method: str = "popular",
        fallback_level: int = 3,
    ) -> dict[str, Any]:
        """L3: 全局热门推荐."""
        stmt = (
            select(Repository)
            .where(Repository.review_status != "rejected")
            .order_by(Repository.trending_rank.asc().nullslast())
            .limit(limit)
        )
        result = await session.execute(stmt)
        repos = result.scalars().all()

        items = [
            {
                "repo": _repo_to_recommendation_dict(r),
                "score": round(1.0 - (i * 0.02), 4),
                "method": method,
                "reason": "本周热门项目",
            }
            for i, r in enumerate(repos)
        ]

        return {"items": items, "method": method, "fallback_level": fallback_level}


def _repo_to_recommendation_dict(repo: Repository) -> dict[str, Any]:
    """将 Repository ORM 对象转换为推荐响应字典."""
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
        "readme_summary": repo.readme_summary,
        "key_points": repo.key_points,
        "tags": repo.tags,
        "trending_rank": repo.trending_rank,
        "source": getattr(repo, "source", "github"),
    }


def _generate_cf_reason(
    repo_id: int, user_behaviors: list[UserBehavior]
) -> str:
    """生成协同过滤推荐理由."""
    action_types = {b.action_type for b in user_behaviors}
    if "star" in action_types:
        return "与你收藏的项目相似"
    if "like" in action_types:
        return "与你点赞的项目相似"
    if "view" in action_types:
        return "与你浏览过的项目相似"
    return "基于你的行为偏好"
