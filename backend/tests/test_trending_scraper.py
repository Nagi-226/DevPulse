"""Trending 爬虫单元测试."""

from __future__ import annotations

import pytest

from devpulse.services.trending_scraper import TrendingScraper

SAMPLE_HTML_BOX_ROW = """
<article class="Box-row">
  <h2 class="h3 lh-condensed">
    <a href="/test-owner/test-repo" class="Link">test-owner / test-repo</a>
  </h2>
  <p class="col-9 color-fg-muted my-1 pr-4">A sample test repository for trending</p>
  <div class="f6 color-fg-muted mt-2">
    <span class="d-inline-block mr-3">
      <span itemprop="programmingLanguage">Python</span>
    </span>
    <span class="d-inline-block float-sm-right">
      <span class="d-inline-block mr-3">
        1,234 stars this week
      </span>
      <span class="d-inline-block mr-3">
        56 forks this week
      </span>
    </span>
  </div>
  <a href="/test-owner/test-repo/stargazers" aria-label="42,000 users starred this repository">
    Stargazers
  </a>
</article>
"""

SAMPLE_HTML_EMPTY = (
    """<div class="Box"><div class="blankslate">No trending repositories</div></div>"""
)


@pytest.mark.asyncio
async def test_parse_single_repo():
    """用模拟 HTML 片段测试解析逻辑."""
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(f"<html><body>{SAMPLE_HTML_BOX_ROW}</body></html>")

        article = await page.query_selector("article.Box-row")
        assert article is not None

        scraper = TrendingScraper(headless=True)
        result = await scraper._parse_single_repo(article, rank=1)

        assert result["rank"] == 1
        assert result["owner"] == "test-owner"
        assert result["repo_name"] == "test-repo"
        assert result["url"] == "https://github.com/test-owner/test-repo"
        assert result["description"] == "A sample test repository for trending"
        assert result["language"] == "Python"
        assert result["stars_since"] == 1234
        assert result["forks_since"] == 56
        assert result["total_stars"] == 42000

        await browser.close()


@pytest.mark.asyncio
async def test_parse_trending_empty():
    """Trending 页面无数据时的处理."""
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(f"<html><body>{SAMPLE_HTML_EMPTY}</body></html>")

        scraper = TrendingScraper(headless=True)
        result = await scraper._parse_trending_page(page)

        assert isinstance(result, list)
        assert len(result) == 0

        await browser.close()


def test_parse_number():
    """测试数字解析."""
    assert TrendingScraper._parse_number("1,234 stars this week") == 1234
    assert TrendingScraper._parse_number("56 forks") == 56
    assert TrendingScraper._parse_number("no numbers") == 0
    assert TrendingScraper._parse_number("") == 0
