"""TrendingAnalyzer — 数据分析 Agent。

负责数据清洗、去重、分类、语言/Stars/Topics 统计。
MetaGPT 角色映射：Architect
"""

from __future__ import annotations

import logging
from typing import Any

from devpulse.agents.base import Role

logger = logging.getLogger(__name__)


class TrendingAnalyzer(Role):
    """Trending 数据分析 Agent。

    对爬取的原始数据进行清洗、去重、分类和统计。
    """

    def __init__(self):
        super().__init__(
            name="TrendingAnalyzer",
            profile="数据分析架构师",
            goal="清洗、去重、分类 GitHub Trending 数据，生成结构化项目清单",
            constraints="不丢失数据，保持数据完整性",
        )

    async def _act(self, repos: list[dict[str, Any]]) -> dict[str, Any]:
        """执行数据分析。

        Args:
            repos: 原始项目数据列表（来自 Crawler Agent）

        Returns:
            结构化分析结果，包含统计信息和清洗后的项目清单
        """
        logger.info(f"[{self.name}] 开始分析 {len(repos)} 个项目")

        # 模拟分析 — 后续版本接入真实分析逻辑
        languages: dict[str, int] = {}
        total_stars = 0

        for repo in repos:
            lang = repo.get("language", "Unknown")
            languages[lang] = languages.get(lang, 0) + 1
            total_stars += repo.get("stars", 0)

        result: dict[str, Any] = {
            "total_repos": len(repos),
            "total_stars": total_stars,
            "language_distribution": languages,
            "cleaned_repos": repos,
            "analysis_notes": "Mock analysis — 后续版本接入真实分析逻辑",
        }

        logger.info(
            f"[{self.name}] 分析完成: {len(repos)} 个项目, "
            f"{len(languages)} 种语言, {total_stars} 总星数"
        )
        return result
