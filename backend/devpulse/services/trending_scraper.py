"""GitHub Trending 页面爬虫 —— 基于 Playwright."""

from __future__ import annotations

import logging
from typing import Any

from playwright.async_api import Browser, async_playwright

logger = logging.getLogger(__name__)


class TrendingScraper:
    """GitHub Trending 页面异步爬虫.

    Args:
        headless: 是否无头模式运行浏览器.
    """

    BASE_URL = "https://github.com/trending"

    def __init__(self, headless: bool = True) -> None:
        self._headless = headless
        self._playwright = None
        self._browser: Browser | None = None

    async def _ensure_browser(self) -> Browser:
        """懒惰初始化浏览器实例."""
        if self._browser is None:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=self._headless)
        return self._browser

    async def scrape_trending(
        self, language: str = "", since: str = "weekly"
    ) -> list[dict[str, Any]]:
        """爬取 GitHub Trending 页面仓库列表.

        Args:
            language: 语言过滤，空字符串表示全语言.
            since: 时间范围 daily/weekly/monthly.

        Returns:
            仓库信息列表，每项包含 rank/owner/repo_name/url/description/language/
            total_stars/stars_since/forks_since.
        """
        url = self.BASE_URL
        if language:
            url += f"/{language}"
        url += f"?since={since}"

        logger.info("Scraping GitHub Trending: %s", url)
        browser = await self._ensure_browser()
        page = await browser.new_page()
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)

            # 等待 Box-row 元素出现
            await page.wait_for_selector("article.Box-row", timeout=15000)

            repos = await self._parse_trending_page(page)
            logger.info("Scraped %d trending repos from %s", len(repos), url)
            return repos
        finally:
            await page.close()

    async def _parse_trending_page(self, page) -> list[dict[str, Any]]:  # type: ignore[no-untyped-def]
        """解析 Trending 页面 DOM，提取仓库列表."""
        articles = await page.query_selector_all("article.Box-row")
        repos: list[dict[str, Any]] = []

        for idx, article in enumerate(articles):
            try:
                repo_info = await self._parse_single_repo(article, rank=idx + 1)
                repos.append(repo_info)
            except Exception:
                logger.exception("Failed to parse trending repo at rank %d", idx + 1)

        return repos

    async def _parse_single_repo(self, article, rank: int) -> dict[str, Any]:  # type: ignore[no-untyped-def]
        """解析单个 .Box-row 元素."""
        # owner/repo_name
        h2 = await article.query_selector("h2 a")
        href = await h2.get_attribute("href") if h2 else ""
        full_name = href.strip("/") if href else ""
        parts = full_name.split("/")
        owner = parts[0] if len(parts) >= 1 else ""
        repo_name = parts[1] if len(parts) >= 2 else ""

        # description
        desc_el = await article.query_selector("p")
        description = (await desc_el.inner_text()).strip() if desc_el else ""

        # language
        lang_el = await article.query_selector('[itemprop="programmingLanguage"]')
        language = (await lang_el.inner_text()).strip() if lang_el else ""

        # stars / forks
        total_stars = 0
        stars_since = 0
        forks_since = 0

        # 统计行通常位于 flex 容器中
        stat_spans = await article.query_selector_all("span.d-inline-block")
        for span in stat_spans:
            text = (await span.inner_text()).strip()
            # 例如 " 42,123 stars this week"
            if "star" in text:
                stars_since = self._parse_number(text)
            elif "fork" in text:
                forks_since = self._parse_number(text)

        # 尝试从链接的 aria-label 或标题属性获取总 star 数
        star_link = await article.query_selector("a[href$='/stargazers']")
        if star_link:
            aria = await star_link.get_attribute("aria-label")
            if aria:
                total_stars = self._parse_number(aria)

        return {
            "rank": rank,
            "owner": owner,
            "repo_name": repo_name,
            "url": f"https://github.com/{full_name}",
            "description": description,
            "language": language,
            "total_stars": total_stars,
            "stars_since": stars_since,
            "forks_since": forks_since,
        }

    async def scrape_repo_readme(self, owner: str, repo: str) -> str:
        """爬取仓库页面 README 内容（绕过 API 限制）.

        Args:
            owner: 仓库所有者.
            repo: 仓库名称.

        Returns:
            README 纯文本内容.
        """
        url = f"https://github.com/{owner}/{repo}"
        browser = await self._ensure_browser()
        page = await browser.new_page()
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)

            # GitHub 页面 README 通常位于 article.markdown-body 或 #readme 容器
            readme_el = await page.query_selector(
                "#readme article.markdown-body, .Box-body .markdown-body"
            )
            if readme_el:
                text = await readme_el.inner_text()
                return text

            return ""
        finally:
            await page.close()

    async def close(self) -> None:
        """关闭浏览器实例与 Playwright."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self._browser = None
        self._playwright = None

    @staticmethod
    def _parse_number(text: str) -> int:
        """从文本中提取数字，支持逗号分隔格式."""
        import re

        match = re.search(r"[\d,]+", text)
        if not match:
            return 0
        return int(match.group().replace(",", ""))
