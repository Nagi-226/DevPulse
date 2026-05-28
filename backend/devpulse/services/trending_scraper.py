"""GitHub Trending 页面爬虫 —— 基于 Playwright."""

from __future__ import annotations

import logging
from typing import Any, TYPE_CHECKING

from playwright.async_api import Browser, async_playwright

if TYPE_CHECKING:
    from devpulse.services.github_client import GitHubClient

logger = logging.getLogger(__name__)


class TrendingScraper:
    """GitHub Trending 页面异步爬虫.

    Args:
        headless: 是否无头模式运行浏览器.
        github_client: 可选的 GitHubClient，用于补全 API 数据.
    """

    BASE_URL = "https://github.com/trending"

    def __init__(self, headless: bool = True, github_client: "GitHubClient | None" = None) -> None:
        self._headless = headless
        self._github_client = github_client
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
            total_stars/stars_since/forks/forks_since/open_issues/created_at/updated_at.
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
        """解析单个 .Box-row 元素，提取完整仓库信息.

        先通过 DOM 解析获取基础字段，再通过 GitHub REST API 补全
        total_stars / forks / open_issues / created_at / updated_at。
        API 调用失败时保留 DOM 解析结果作为 fallback，不中断整体爬取。
        """
        # ── DOM 解析 ──────────────────────────────────────
        h2 = await article.query_selector("h2 a")
        href = await h2.get_attribute("href") if h2 else ""
        full_name = href.strip("/") if href else ""
        parts = full_name.split("/")
        owner = parts[0] if len(parts) >= 1 else ""
        repo_name = parts[1] if len(parts) >= 2 else ""

        desc_el = await article.query_selector("p")
        description = (await desc_el.inner_text()).strip() if desc_el else ""

        lang_el = await article.query_selector('[itemprop="programmingLanguage"]')
        language = (await lang_el.inner_text()).strip() if lang_el else ""

        total_stars = 0
        stars_since = 0
        forks_since = 0

        # 统计行：stars_since / forks_since
        stat_spans = await article.query_selector_all("span.d-inline-block")
        for span in stat_spans:
            text = (await span.inner_text()).strip()
            if "star" in text.lower():
                stars_since = self._parse_number(text)
            elif "fork" in text.lower():
                forks_since = self._parse_number(text)

        # 尝试多种方式获取总 Star 数
        # 方式 1: stargazers 链接的 aria-label
        star_link = await article.query_selector("a[href$='/stargazers']")
        if star_link:
            aria = await star_link.get_attribute("aria-label")
            if aria:
                total_stars = self._parse_number(aria)

        # 方式 2: svg 旁边最近的文本节点（部分 Trending 页面格式）
        if total_stars == 0:
            star_svg_parent = await article.query_selector(
                "svg.octicon-star"
            )
            if star_svg_parent:
                parent = await star_svg_parent.evaluate(
                    "el => el.closest('a')?.innerText || ''"
                )
                if parent:
                    total_stars = self._parse_number(parent)

        # 构造基础结果
        result = {
            "rank": rank,
            "owner": owner,
            "repo_name": repo_name,
            "url": f"https://github.com/{full_name}",
            "description": description,
            "language": language,
            "total_stars": total_stars,
            "stars_since": stars_since,
            "forks": 0,
            "forks_since": forks_since,
            "open_issues": 0,
            "created_at": None,
            "updated_at": None,
        }

        # ── GitHub API 补全（可选，不阻塞主流程）──────────
        if self._github_client and owner and repo_name:
            try:
                api_data = await self._github_client.fetch_repo(owner, repo_name)
                # 使用 API 返回值覆盖 DOM 解析结果
                result["total_stars"] = api_data.get("total_stars", result["total_stars"])
                result["forks"] = api_data.get("forks", 0)
                result["open_issues"] = api_data.get("open_issues", 0)
                result["created_at"] = api_data.get("created_at")
                result["updated_at"] = api_data.get("updated_at")
                # 如果 API 返回了更准确的语言，也使用 API 的值
                if api_data.get("language"):
                    result["language"] = api_data["language"]
            except Exception:
                logger.debug(
                    "GitHub API fallback failed for %s/%s, using DOM data",
                    owner, repo_name,
                )

        return result

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
