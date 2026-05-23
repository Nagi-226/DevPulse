"""存储服务编排单元测试."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from devpulse.core.database import Database
from devpulse.services.storage import StorageService


@pytest.fixture
async def db():
    """内存 SQLite 数据库 fixture."""
    database = Database("sqlite+aiosqlite:///:memory:", echo=False)
    await database.create_tables()
    yield database
    await database.close()


@pytest.fixture
def mock_crawler() -> AsyncMock:
    """Mock CrawlerService."""
    crawler = AsyncMock()
    crawler.crawl_trending_repos = AsyncMock(return_value=[])
    return crawler


@pytest.fixture
def mock_summarizer() -> AsyncMock:
    """Mock Summarizer."""
    summarizer = AsyncMock()
    summarizer.summarize_batch = AsyncMock(return_value=[])
    summarizer.generate_weekly_overview = AsyncMock(return_value="Weekly overview text")
    return summarizer


@pytest.mark.asyncio
async def test_crawl_and_store_empty(db, mock_crawler, mock_summarizer):
    """测试爬取结果为空时不报错."""
    mock_crawler.crawl_trending_repos.return_value = []

    service = StorageService(db, mock_crawler, mock_summarizer)
    results = await service.crawl_and_store_trending(
        language="Python", since="weekly", limit=25
    )

    assert results == []
    mock_crawler.crawl_trending_repos.assert_awaited_once()


@pytest.mark.asyncio
async def test_crawl_and_store(db, mock_crawler, mock_summarizer):
    """测试爬取数据后正确存储并返回."""
    mock_crawler.crawl_trending_repos.return_value = [
        {
            "full_name": "org/repo1",
            "owner": "org",
            "name": "repo1",
            "description": "First repo",
            "language": "Python",
            "total_stars": 1000,
            "stars_since": 50,
            "forks": 200,
            "forks_since": 10,
            "topics": ["ai", "ml"],
            "open_issues": 3,
            "created_at": "2025-01-01",
            "updated_at": "2025-06-01",
            "url": "https://github.com/org/repo1",
            "has_readme": True,
            "readme_content": "# README",
        },
        {
            "full_name": "org/repo2",
            "owner": "org",
            "name": "repo2",
            "description": "Second repo",
            "language": "Go",
            "total_stars": 800,
            "stars_since": 30,
            "forks": 150,
            "forks_since": 8,
            "topics": ["cloud"],
            "open_issues": 1,
            "created_at": "2025-02-01",
            "updated_at": "2025-06-02",
            "url": "https://github.com/org/repo2",
            "has_readme": False,
            "readme_content": None,
        },
    ]

    service = StorageService(db, mock_crawler, mock_summarizer)
    results = await service.crawl_and_store_trending(
        language="", since="weekly", limit=25
    )

    assert len(results) == 2
    assert results[0]["full_name"] == "org/repo1"
    assert results[0]["total_stars"] == 1000
    assert results[0]["stars_since"] == 50
    assert results[1]["full_name"] == "org/repo2"

    # 验证 trending_rank 已设置
    async with db.get_session() as session:
        from sqlalchemy import select

        from devpulse.core.models import Repository

        result = await session.execute(
            select(Repository).order_by(Repository.trending_rank)
        )
        repos = result.scalars().all()
        assert len(repos) == 2
        assert repos[0].trending_rank == 1
        assert repos[0].trending_since == "weekly"
        assert repos[1].trending_rank == 2


@pytest.mark.asyncio
async def test_summarize_and_update_no_repos(db, mock_crawler, mock_summarizer):
    """测试无待摘要项目时返回 0."""
    service = StorageService(db, mock_crawler, mock_summarizer)
    count = await service.summarize_and_update(repo_ids=None, batch_size=5)
    assert count == 0


@pytest.mark.asyncio
async def test_summarize_and_update(db, mock_crawler, mock_summarizer):
    """测试摘要生成和更新流程."""
    # 先存入一条待摘要数据
    async with db.get_session() as session:
        from devpulse.core.repository import RepositoryDAO

        dao = RepositoryDAO(session)
        await dao.create_or_update(
            {
                "full_name": "org/to-summarize",
                "owner": "org",
                "name": "to-summarize",
                "description": "A repo to summarize",
                "language": "Python",
                "total_stars": 500,
                "stars_since": 20,
                "topics": ["test"],
            }
        )

    mock_summarizer.summarize_batch.return_value = [
        {
            "full_name": "org/to-summarize",
            "summary": "This is a summary",
            "key_points": ["Point 1", "Point 2"],
            "tags": ["tag1", "tag2"],
        }
    ]

    service = StorageService(db, mock_crawler, mock_summarizer)
    count = await service.summarize_and_update(repo_ids=None, batch_size=5)

    assert count == 1
    mock_summarizer.summarize_batch.assert_awaited_once()

    # 验证摘要已写入
    async with db.get_session() as session:
        from devpulse.core.repository import RepositoryDAO

        dao = RepositoryDAO(session)
        repo = await dao.get_by_full_name("org/to-summarize")
        assert repo.readme_summary == "This is a summary"
        assert repo.key_points == ["Point 1", "Point 2"]
        assert repo.tags == ["tag1", "tag2"]


@pytest.mark.asyncio
async def test_summarize_and_update_with_repo_ids(db, mock_crawler, mock_summarizer):
    """测试指定 repo_ids 的摘要生成."""
    async with db.get_session() as session:
        from devpulse.core.repository import RepositoryDAO

        dao = RepositoryDAO(session)
        repo = await dao.create_or_update(
            {
                "full_name": "org/target-repo",
                "owner": "org",
                "name": "target-repo",
                "description": "Target repo",
                "language": "Rust",
                "total_stars": 300,
            }
        )
        target_id = repo.id  # type: ignore[assignment]

    mock_summarizer.summarize_batch.return_value = [
        {
            "full_name": "org/target-repo",
            "summary": "Rust summary",
            "key_points": ["Fast", "Safe"],
            "tags": ["rust", "systems"],
        }
    ]

    service = StorageService(db, mock_crawler, mock_summarizer)
    count = await service.summarize_and_update(repo_ids=[target_id], batch_size=5)

    assert count == 1
    mock_summarizer.summarize_batch.assert_awaited_once()


@pytest.mark.asyncio
async def test_generate_weekly_report(db, mock_crawler, mock_summarizer):
    """测试周报生成逻辑."""
    week_start = datetime(2025, 1, 6)

    # 存入 trending 数据
    now = datetime.now()
    async with db.get_session() as session:
        from devpulse.core.repository import RepositoryDAO

        dao = RepositoryDAO(session)
        for i in range(1, 6):
            await dao.create_or_update(
                {
                    "full_name": f"trending/weekly-repo{i}",
                    "owner": "trending",
                    "name": f"weekly-repo{i}",
                    "description": f"Weekly repo {i}",
                    "language": "Python",
                    "total_stars": 1000 + i * 100,
                    "trending_rank": i,
                    "trending_since": "weekly",
                    "crawled_at": now,
                    "readme_summary": f"Summary of repo {i}",
                }
            )

    mock_summarizer.generate_weekly_overview.return_value = "This week's AI trends highlight..."

    service = StorageService(db, mock_crawler, mock_summarizer)
    result = await service.generate_weekly_report(
        week_start=week_start, language_filter="Python"
    )

    assert result["total_repos"] == 5
    assert result["overview_text"] == "This week's AI trends highlight..."
    assert result["week_start"] == week_start
    mock_summarizer.generate_weekly_overview.assert_awaited_once()


@pytest.mark.asyncio
async def test_generate_weekly_report_empty(db, mock_crawler, mock_summarizer):
    """测试无 trending 数据时周报生成."""
    week_start = datetime(2025, 1, 6)

    service = StorageService(db, mock_crawler, mock_summarizer)
    result = await service.generate_weekly_report(
        week_start=week_start, language_filter=None
    )

    assert result["total_repos"] == 0
    assert result["overview_text"] == ""


@pytest.mark.asyncio
async def test_get_weekly_report_html(db, mock_crawler, mock_summarizer):
    """测试 HTML 周报生成."""
    week_start = datetime(2025, 1, 6)
    week_end = datetime(2025, 1, 12)

    # 先存入 repos
    now = datetime.now()
    async with db.get_session() as session:
        from devpulse.core.repository import RepositoryDAO, WeeklyReportDAO

        repo_dao = RepositoryDAO(session)
        report_dao = WeeklyReportDAO(session)

        repo1 = await repo_dao.create_or_update(
            {
                "full_name": "org/html-repo1",
                "owner": "org",
                "name": "html-repo1",
                "description": "HTML repo 1",
                "language": "Python",
                "total_stars": 2000,
                "readme_summary": "Summary for HTML",
                "trending_rank": 1,
                "trending_since": "weekly",
                "crawled_at": now,
            }
        )

        report = await report_dao.create_weekly_report(
            week_start=week_start,
            week_end=week_end,
            language_filter=None,
            total_repos=1,
            top_repos=[repo1.id],  # type: ignore[list-item]
            overview_text="HTML weekly overview",
        )
        report_id = report.id  # type: ignore[assignment]

    service = StorageService(db, mock_crawler, mock_summarizer)
    html = await service.get_weekly_report_html(report_id)

    assert isinstance(html, str)
    assert "<html" in html
    assert "HTML weekly overview" in html
    assert "org/html-repo1" in html
    assert "2000 stars" in html


@pytest.mark.asyncio
async def test_get_weekly_report_html_not_found(db, mock_crawler, mock_summarizer):
    """测试不存在的周报 HTML."""
    service = StorageService(db, mock_crawler, mock_summarizer)
    html = await service.get_weekly_report_html(9999)

    assert "Report Not Found" in html
