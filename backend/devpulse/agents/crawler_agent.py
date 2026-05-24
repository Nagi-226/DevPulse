"""GitHubTrendingCrawler — 数据采集 Agent。

负责抓取 GitHub Trending 页面，获取原始项目数据。
MetaGPT 角色映射：Engineer
"""

from __future__ import annotations

import logging
from typing import Any

from devpulse.agents.base import Role

logger = logging.getLogger(__name__)


class GitHubTrendingCrawler(Role):
    """GitHub Trending 数据采集 Agent。

    抓取 GitHub Trending 页面，返回原始项目列表。
    """

    def __init__(self):
        super().__init__(
            name="GitHubTrendingCrawler",
            profile="数据采集工程师",
            goal="抓取 GitHub Trending 页面，获取本周热门 AI/ML 项目",
            constraints="不修改源数据，保持原始格式",
        )

    async def _act(
        self,
        language: str = "",
        since: str = "weekly",
        top_n: int = 25,
    ) -> list[dict[str, Any]]:
        """执行数据采集。

        Args:
            language: 编程语言过滤（空字符串表示全语言）
            since: 时间范围（daily/weekly/monthly）
            top_n: 返回前 N 个项目

        Returns:
            原始项目数据列表
        """
        logger.info(
            f"[{self.name}] 开始采集 GitHub Trending: "
            f"language={language or 'all'}, since={since}, top_n={top_n}"
        )

        # 模拟数据 — 后续版本接入真实爬虫
        mock_repos: list[dict[str, Any]] = [
            {
                "name": "mock-project-1",
                "full_name": "mock-org/mock-project-1",
                "description": "A mock trending project for MetaGPT pipeline testing",
                "language": language or "Python",
                "stars": 1234,
                "forks": 567,
                "url": "https://github.com/mock-org/mock-project-1",
            },
            {
                "name": "mock-project-2",
                "full_name": "mock-org/mock-project-2",
                "description": "Another mock project for pipeline validation",
                "language": language or "TypeScript",
                "stars": 2345,
                "forks": 890,
                "url": "https://github.com/mock-org/mock-project-2",
            },
        ]

        logger.info(f"[{self.name}] 采集完成，共 {len(mock_repos)} 个项目")
        return mock_repos
