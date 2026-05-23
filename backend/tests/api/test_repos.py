"""REST API 端点单元测试."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from devpulse.core.database import Database
from devpulse.main import app


@pytest.fixture
async def db():
    """内存 SQLite 数据库 fixture."""
    database = Database("sqlite+aiosqlite:///:memory:", echo=False)
    await database.create_tables()
    yield database
    await database.close()


@pytest.fixture
async def client(db):
    """FastAPI 测试客户端，注入 mock 数据库."""
    # 覆盖 app.state.db
    app.state.db = db
    # 注入空的 storage_service 避免依赖
    mock_storage = AsyncMock()
    mock_storage.crawl_and_store_trending = AsyncMock()
    mock_storage.summarize_and_update = AsyncMock()
    mock_storage.get_weekly_report_html = AsyncMock(return_value="<html>mock</html>")
    app.state.storage_service = mock_storage

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
async def sample_repos(db):
    """预置一些测试仓库数据."""
    now = datetime.now()
    async with db.get_session() as session:
        from devpulse.core.repository import RepositoryDAO

        dao = RepositoryDAO(session)
        repos = []
        for i in range(1, 6):
            repo = await dao.create_or_update(
                {
                    "full_name": f"org/repo{i}",
                    "owner": "org",
                    "name": f"repo{i}",
                    "description": f"Description {i}",
                    "language": "Python" if i % 2 else "Go",
                    "total_stars": 1000 + i * 100,
                    "stars_since": i * 10,
                    "forks": 100 + i * 20,
                    "forks_since": i * 5,
                    "topics": ["ai", "ml"] if i % 2 else ["cloud", "go"],
                    "open_issues": i,
                    "created_at": now,
                    "updated_at": now,
                    "url": f"https://github.com/org/repo{i}",
                    "has_readme": True,
                    "readme_summary": f"Summary {i}",
                    "key_points": [f"Point {i}-1", f"Point {i}-2"],
                    "tags": [f"tag{i}-1", f"tag{i}-2"],
                    "crawled_at": now,
                    "summarized_at": now,
                    "trending_rank": i,
                    "trending_since": "weekly",
                }
            )
            repos.append(repo)
        return repos


@pytest.mark.asyncio
async def test_list_repos(client, sample_repos):
    """测试列出仓库（分页和语言过滤）."""
    response = await client.get("/repos/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert data["page"] == 1
    assert data["limit"] == 25
    assert len(data["items"]) == 5

    # 验证字段
    item = data["items"][0]
    assert "id" in item
    assert "full_name" in item
    assert "owner" in item
    assert "name" in item
    assert "description" in item
    assert "language" in item
    assert "total_stars" in item
    assert "stars_since" in item
    assert "forks" in item
    assert "topics" in item
    assert "trending_rank" in item
    assert "trending_since" in item
    assert "summarized_at" in item

    # 分页测试
    response = await client.get("/repos/", params={"page": 2, "limit": 2})
    data = response.json()
    assert data["total"] == 5
    assert data["page"] == 2
    assert data["limit"] == 2
    assert len(data["items"]) == 2

    # 语言过滤
    response = await client.get("/repos/", params={"language": "Go"})
    data = response.json()
    assert data["total"] == 2  # 第 2、4 个是 Go
    assert all(item["language"] == "Go" for item in data["items"])


@pytest.mark.asyncio
async def test_get_trending(client, sample_repos):
    """测试获取 trending 列表."""
    response = await client.get("/repos/trending")
    assert response.status_code == 200
    data = response.json()
    assert data["since"] == "weekly"
    assert data["total"] == 5
    assert len(data["items"]) == 5

    # 按 ranking 排序
    ranks = [item["trending_rank"] for item in data["items"]]
    assert ranks == [1, 2, 3, 4, 5]

    item = data["items"][0]
    assert item["full_name"] == "org/repo1"
    assert item["summary"] == "Summary 1"
    assert item["key_points"] == ["Point 1-1", "Point 1-2"]
    assert item["tags"] == ["tag1-1", "tag1-2"]

    # 自定义 since 和 limit
    response = await client.get("/repos/trending", params={"since": "daily", "limit": 2})
    data = response.json()
    assert data["since"] == "daily"
    assert data["total"] == 0  # 没有 daily trending 数据
    assert len(data["items"]) == 0


@pytest.mark.asyncio
async def test_get_repo_detail(client, sample_repos):
    """测试获取单个仓库详情."""
    response = await client.get("/repos/org/repo3")
    assert response.status_code == 200
    data = response.json()

    assert data["full_name"] == "org/repo3"
    assert data["owner"] == "org"
    assert data["name"] == "repo3"
    assert data["description"] == "Description 3"
    assert data["language"] == "Python"
    assert data["total_stars"] == 1300
    assert data["stars_since"] == 30
    assert data["forks"] == 160
    assert data["forks_since"] == 15
    assert data["open_issues"] == 3
    assert data["topics"] == ["ai", "ml"]
    assert data["has_readme"] is True
    assert data["readme_summary"] == "Summary 3"
    assert data["key_points"] == ["Point 3-1", "Point 3-2"]
    assert data["tags"] == ["tag3-1", "tag3-2"]
    assert data["trending_rank"] == 3
    assert data["trending_since"] == "weekly"
    assert "crawled_at" in data
    assert "summarized_at" in data
    assert "created_at" in data
    assert "updated_at" in data

    # 不存在的仓库
    response = await client.get("/repos/nonexistent/repo")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_crawl_endpoint(client):
    """测试触发爬虫（后台异步任务）."""
    response = await client.post(
        "/repos/crawl",
        params={"language": "Python", "since": "weekly", "limit": 25},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Crawl task started"
    assert data["language"] == "Python"
    assert data["since"] == "weekly"

    # 验证后台任务已添加（mock 调用）
    storage_service = app.state.storage_service
    # 后台任务在测试中可能立即执行，检查是否被调用过
    # assert_not_awaited() 在立即执行时会失败，改为检查是否被调用
    storage_service.crawl_and_store_trending.assert_called_once_with(
        language="Python", since="weekly", limit=25
    )


@pytest.mark.asyncio
async def test_summarize_endpoint(client, sample_repos):
    """测试触发单个仓库摘要（后台异步任务）."""
    response = await client.post("/repos/org/repo2/summarize")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Summarize task started"
    assert data["full_name"] == "org/repo2"

    # 不存在的仓库（后台任务会记录警告）
    response = await client.post("/repos/nonexistent/repo/summarize")
    assert response.status_code == 200  # 仍返回 200，后台处理


@pytest.mark.asyncio
async def test_list_weekly_reports(client, db):
    """测试列出周报."""
    # 先创建周报数据
    async with db.get_session() as session:
        from devpulse.core.repository import WeeklyReportDAO

        dao = WeeklyReportDAO(session)
        await dao.create_weekly_report(
            week_start=datetime(2025, 1, 6),
            week_end=datetime(2025, 1, 12),
            language_filter="Python",
            total_repos=25,
            top_repos=[1, 2, 3],
            overview_text="Week 1 overview",
        )
        await dao.create_weekly_report(
            week_start=datetime(2025, 1, 13),
            week_end=datetime(2025, 1, 19),
            language_filter=None,
            total_repos=30,
            top_repos=[4, 5],
            overview_text="Week 2 overview",
        )
        # 已发布的周报
        report3 = await dao.create_weekly_report(
            week_start=datetime(2025, 1, 20),
            week_end=datetime(2025, 1, 26),
            language_filter="Go",
            total_repos=15,
            top_repos=[6],
            overview_text="Week 3 overview",
        )
        await dao.mark_published(report3.id)  # type: ignore[arg-type]

    response = await client.get("/repos/weekly-reports")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3

    # 按时间降序排列（最新在前）
    assert data["items"][0]["language_filter"] == "Go"  # 第三周
    assert data["items"][1]["language_filter"] is None  # 第二周
    assert data["items"][2]["language_filter"] == "Python"  # 第一周

    # 仅已发布
    response = await client.get("/repos/weekly-reports", params={"published_only": True})
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["language_filter"] == "Go"
    assert data["items"][0]["published"] is True

    # 限制数量
    response = await client.get("/repos/weekly-reports", params={"limit": 2})
    data = response.json()
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_get_weekly_report_detail_json(client, db):
    """测试获取周报详情（JSON 格式）."""
    async with db.get_session() as session:
        from devpulse.core.repository import WeeklyReportDAO

        dao = WeeklyReportDAO(session)
        report = await dao.create_weekly_report(
            week_start=datetime(2025, 2, 3),
            week_end=datetime(2025, 2, 9),
            language_filter="Rust",
            total_repos=12,
            top_repos=[7, 8, 9],
            overview_text="Rust weekly trends",
        )
        report_id = report.id  # type: ignore[assignment]

    response = await client.get(f"/repos/weekly-reports/{report_id}")
    assert response.status_code == 200
    data = response.json()

    assert data["id"] == report_id
    assert data["language_filter"] == "Rust"
    assert data["total_repos"] == 12
    assert data["top_repos"] == [7, 8, 9]
    assert data["overview_text"] == "Rust weekly trends"
    assert data["published"] is False
    assert data["published_at"] is None
    assert "generated_at" in data

    # 不存在的周报
    response = await client.get("/repos/weekly-reports/9999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_weekly_report_detail_html(client, db):
    """测试获取周报详情（HTML 格式）."""
    async with db.get_session() as session:
        from devpulse.core.repository import RepositoryDAO, WeeklyReportDAO

        repo_dao = RepositoryDAO(session)
        report_dao = WeeklyReportDAO(session)

        repo = await repo_dao.create_or_update(
            {
                "full_name": "org/html-test",
                "owner": "org",
                "name": "html-test",
                "description": "HTML test repo",
                "language": "TypeScript",
                "total_stars": 1500,
                "readme_summary": "Test summary for HTML",
            }
        )

        report = await report_dao.create_weekly_report(
            week_start=datetime(2025, 3, 1),
            week_end=datetime(2025, 3, 7),
            language_filter=None,
            total_repos=5,
            top_repos=[repo.id],  # type: ignore[list-item]
            overview_text="HTML test overview",
        )
        report_id = report.id  # type: ignore[assignment]

    response = await client.get(
        f"/repos/weekly-reports/{report_id}",
        params={"format": "html"},
        headers={"Accept": "text/html"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    html = response.text
    assert "<html" in html
    # mock 返回固定值
    assert html == "<html>mock</html>"

    # 不存在的周报 HTML（mock 也返回固定内容，需单独设置）
    response = await client.get("/repos/weekly-reports/9999", params={"format": "html"})
    assert response.status_code == 200
    assert "mock" in response.text
