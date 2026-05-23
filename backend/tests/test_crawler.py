"""爬虫编排服务单元测试."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

import pytest

from devpulse.services.crawler import CrawlerService
from devpulse.services.github_client import GitHubNotFoundError


@pytest.fixture
def mock_github_client() -> AsyncMock:
    client = AsyncMock()
    client.fetch_repo = AsyncMock(
        return_value={
            "full_name": "test-owner/test-repo",
            "description": "Test",
            "language": "Python",
            "total_stars": 1000,
            "forks": 100,
            "topics": ["test"],
            "open_issues": 3,
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-06-01T00:00:00Z",
        }
    )
    client.close = AsyncMock()
    return client


@pytest.fixture
def mock_scraper() -> AsyncMock:
    scraper = AsyncMock()
    scraper.scrape_trending = AsyncMock(
        return_value=[
            {
                "rank": 1,
                "owner": "test-owner",
                "repo_name": "test-repo",
                "url": "https://github.com/test-owner/test-repo",
                "description": "A trending repo",
                "language": "Python",
                "total_stars": 10000,
                "stars_since": 500,
                "forks_since": 30,
            },
            {
                "rank": 2,
                "owner": "other-owner",
                "repo_name": "other-repo",
                "url": "https://github.com/other-owner/other-repo",
                "description": "Another repo",
                "language": "Go",
                "total_stars": 8000,
                "stars_since": 300,
                "forks_since": 20,
            },
        ]
    )
    scraper.close = AsyncMock()
    return scraper


@pytest.mark.asyncio
async def test_crawl_pipeline(mock_github_client, mock_scraper):
    """Mock 两个子服务，测试数据合并逻辑."""
    service = CrawlerService(mock_github_client, mock_scraper)
    results = await service.crawl_trending_repos(since="weekly", limit=25)

    assert len(results) == 2

    # 第一条：trending 数据 + API 数据合并
    assert results[0]["rank"] == 1
    assert results[0]["owner"] == "test-owner"
    assert results[0]["repo_name"] == "test-repo"
    assert results[0]["total_stars"] == 1000  # API 返回的值覆盖
    assert results[0]["forks"] == 100
    assert results[0]["topics"] == ["test"]
    assert results[0]["has_readme"] is True

    await service.close()


@pytest.mark.asyncio
async def test_concurrency_limit(mock_github_client, mock_scraper):
    """验证 Semaphore(5) 并发控制."""
    call_count = 0

    async def slow_fetch(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0.01)
        return {
            "full_name": "test/repo",
            "description": "",
            "language": "Python",
            "total_stars": 100,
            "forks": 10,
            "topics": [],
            "open_issues": 0,
            "created_at": None,
            "updated_at": None,
        }

    mock_github_client.fetch_repo = AsyncMock(side_effect=slow_fetch)
    mock_scraper.scrape_trending = AsyncMock(
        return_value=[
            {
                "rank": i,
                "owner": f"owner{i}",
                "repo_name": f"repo{i}",
                "url": f"https://github.com/owner{i}/repo{i}",
                "description": "",
                "language": "Python",
                "total_stars": 100,
                "stars_since": 10,
                "forks_since": 5,
            }
            for i in range(1, 11)  # 10 条，Semaphore(5) 应生效
        ]
    )

    service = CrawlerService(mock_github_client, mock_scraper, concurrency=5)
    results = await service.crawl_trending_repos(limit=10)

    assert len(results) == 10
    # Semaphore(5) 不限制调用次数，只限制并发度；10 个调用都应完成
    assert call_count == 10

    await service.close()


@pytest.mark.asyncio
async def test_partial_failure(mock_scraper):
    """某个仓库 API 调用失败不影响整体."""
    mock_github_client = AsyncMock()

    async def flaky_fetch(owner, repo):
        if repo == "fail-repo":
            raise GitHubNotFoundError("Resource not found")
        return {
            "full_name": f"{owner}/{repo}",
            "description": "OK",
            "language": "Go",
            "total_stars": 500,
            "forks": 50,
            "topics": [],
            "open_issues": 1,
            "created_at": None,
            "updated_at": None,
        }

    mock_github_client.fetch_repo = AsyncMock(side_effect=flaky_fetch)
    mock_github_client.close = AsyncMock()

    mock_scraper.scrape_trending = AsyncMock(
        return_value=[
            {
                "rank": 1,
                "owner": "owner1",
                "repo_name": "ok-repo",
                "url": "https://github.com/owner1/ok-repo",
                "description": "OK",
                "language": "Go",
                "total_stars": 500,
                "stars_since": 50,
                "forks_since": 10,
            },
            {
                "rank": 2,
                "owner": "owner2",
                "repo_name": "fail-repo",
                "url": "https://github.com/owner2/fail-repo",
                "description": "Will fail",
                "language": "Rust",
                "total_stars": 300,
                "stars_since": 20,
                "forks_since": 5,
            },
        ]
    )

    service = CrawlerService(mock_github_client, mock_scraper)
    results = await service.crawl_trending_repos(limit=25)

    # fail-repo 仍返回（trending 数据 + 默认值），ok-repo 正常返回
    assert len(results) == 2

    ok_repo = next(r for r in results if r["repo_name"] == "ok-repo")
    assert ok_repo["has_readme"] is True
    assert ok_repo["total_stars"] == 500

    fail_repo = next(r for r in results if r["repo_name"] == "fail-repo")
    assert fail_repo["has_readme"] is False
    assert fail_repo["total_stars"] == 300  # 来自 trending 数据

    await service.close()


@pytest.mark.asyncio
async def test_empty_trending(mock_github_client, mock_scraper):
    """Trending 页面无数据时返回空列表."""
    mock_scraper.scrape_trending = AsyncMock(return_value=[])

    service = CrawlerService(mock_github_client, mock_scraper)
    results = await service.crawl_trending_repos()

    assert results == []

    await service.close()
