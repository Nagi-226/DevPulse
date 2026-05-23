"""统一爬虫服务编排 —— 整合 TrendingScraper + GitHubClient."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from devpulse.services.github_client import (
    GitHubClient,
    GitHubClientError,
    GitHubNotFoundError,
    GitHubRateLimitError,
)
from devpulse.services.trending_scraper import TrendingScraper

logger = logging.getLogger(__name__)


class CrawlerService:
    """GitHub Trending 爬虫编排服务.

    整合 TrendingScraper（页面爬取）与 GitHubClient（API 详情），
    合并两个数据源返回完整仓库信息。

    Args:
        github_client: GitHub API 客户端实例.
        scraper: Trending 页面爬虫实例.
        concurrency: 并发 API 请求数上限.
    """

    def __init__(
        self,
        github_client: GitHubClient,
        scraper: TrendingScraper,
        concurrency: int = 5,
    ) -> None:
        self._github = github_client
        self._scraper = scraper
        self._semaphore = asyncio.Semaphore(concurrency)

    async def crawl_trending_repos(
        self,
        language: str = "",
        since: str = "weekly",
        limit: int = 25,
    ) -> list[dict[str, Any]]:
        """爬取 Trending 列表并补充 API 详情.

        流程：
        1. TrendingScraper 获取 trending 列表
        2. 对每个仓库并发调用 GitHubClient.fetch_repo 补充数据
        3. 合并两个数据源
        4. 返回前 limit 条

        Args:
            language: 语言过滤（空字符串 = 全语言）.
            since: 时间范围 daily/weekly/monthly.
            limit: 返回条数上限.

        Returns:
            合并后的完整仓库信息列表.
        """
        # 1. 爬取 trending 页面
        trending_list = await self._scraper.scrape_trending(language=language, since=since)
        if not trending_list:
            logger.warning("No trending repos found for language=%s since=%s", language, since)
            return []

        # 2. 并发拉取 API 详情
        tasks = []
        for item in trending_list[:limit]:
            tasks.append(self._fetch_and_merge(item))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 3. 过滤失败项
        merged: list[dict[str, Any]] = []
        for result in results:
            if isinstance(result, dict):
                merged.append(result)
            else:
                logger.warning("Skipped a repo due to error: %s", result)

        return merged

    async def _fetch_and_merge(self, trending_item: dict[str, Any]) -> dict[str, Any]:
        """对单个 trending 条目拉取 API 详情并合并."""
        owner = trending_item["owner"]
        repo_name = trending_item["repo_name"]
        merged = dict(trending_item)

        async with self._semaphore:
            try:
                api_data = await self._github.fetch_repo(owner, repo_name)
                merged.update(api_data)
                merged["has_readme"] = True
            except (GitHubNotFoundError, GitHubRateLimitError, GitHubClientError) as exc:
                logger.warning(
                    "GitHub API failed for %s/%s: %s",
                    owner,
                    repo_name,
                    exc,
                )
                merged["has_readme"] = False
                # 确保 total_stars 至少来自 trending 页面
                merged.setdefault("total_stars", trending_item.get("total_stars", 0))
                merged.setdefault("forks", 0)
                merged.setdefault("topics", [])
                merged.setdefault("open_issues", 0)
                merged.setdefault("created_at", None)
                merged.setdefault("updated_at", None)

        return merged

    async def close(self) -> None:
        """关闭子服务."""
        await self._github.close()
        await self._scraper.close()
