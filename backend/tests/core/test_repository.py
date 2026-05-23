"""数据访问层单元测试."""

from datetime import datetime

import pytest

from devpulse.core.database import Database
from devpulse.core.repository import RepositoryDAO, WeeklyReportDAO


@pytest.fixture
async def db():
    """内存 SQLite 数据库 fixture."""
    database = Database("sqlite+aiosqlite:///:memory:", echo=False)
    await database.create_tables()
    yield database
    await database.close()


@pytest.mark.asyncio
async def test_create_or_update(db):
    """验证创建和更新逻辑."""
    now = datetime(2025, 1, 15)
    repo_data = {
        "full_name": "test/create-test",
        "owner": "test",
        "name": "create-test",
        "description": "A test repo",
        "language": "Python",
        "total_stars": 100,
        "crawled_at": now,
    }

    async with db.get_session() as session:
        dao = RepositoryDAO(session)
        repo = await dao.create_or_update(repo_data)

        assert repo.id is not None
        assert repo.full_name == "test/create-test"
        assert repo.owner == "test"
        assert repo.total_stars == 100

        # 第二次 upsert 应该更新
        repo_data["total_stars"] = 200
        repo_data["description"] = "Updated description"
        updated = await dao.create_or_update(repo_data)

        assert updated.id == repo.id  # 相同 ID
        assert updated.total_stars == 200
        assert updated.description == "Updated description"


@pytest.mark.asyncio
async def test_bulk_create_or_update(db):
    """验证批量 upsert."""
    repos_data = [
        {
            "full_name": f"org/repo{i}",
            "owner": "org",
            "name": f"repo{i}",
            "description": f"Repo {i}",
            "language": "Python",
            "total_stars": i * 100,
        }
        for i in range(1, 4)
    ]

    async with db.get_session() as session:
        dao = RepositoryDAO(session)
        results = await dao.bulk_create_or_update(repos_data)

        assert len(results) == 3
        assert results[0].full_name == "org/repo1"
        assert results[1].full_name == "org/repo2"
        assert results[2].full_name == "org/repo3"

        # 重复 upsert 不创建新记录
        repos_data[0]["total_stars"] = 999
        results2 = await dao.bulk_create_or_update(repos_data)
        assert len(results2) == 3
        assert results2[0].total_stars == 999


@pytest.mark.asyncio
async def test_bulk_create_or_update_empty(db):
    """验证空列表不报错."""
    async with db.get_session() as session:
        dao = RepositoryDAO(session)
        results = await dao.bulk_create_or_update([])
        assert results == []


@pytest.mark.asyncio
async def test_get_by_full_name(db):
    """验证按完整仓库名查询."""
    async with db.get_session() as session:
        dao = RepositoryDAO(session)
        await dao.create_or_update(
            {
                "full_name": "microsoft/vscode",
                "owner": "microsoft",
                "name": "vscode",
            }
        )

        repo = await dao.get_by_full_name("microsoft/vscode")
        assert repo is not None
        assert repo.name == "vscode"

        # 不存在的应返回 None
        not_found = await dao.get_by_full_name("nobody/nothing")
        assert not_found is None


@pytest.mark.asyncio
async def test_get_trending_repos(db):
    """验证按排名查询 trending."""
    now = datetime.now()
    async with db.get_session() as session:
        dao = RepositoryDAO(session)

        for i in range(1, 6):
            await dao.create_or_update(
                {
                    "full_name": f"trending/repo{i}",
                    "owner": "trending",
                    "name": f"repo{i}",
                    "total_stars": 1000 - i * 10,
                    "trending_rank": i,
                    "trending_since": "weekly",
                    "crawled_at": now,
                }
            )

        results = await dao.get_trending_repos(since="weekly", limit=3)
        assert len(results) == 3
        assert results[0].trending_rank == 1
        assert results[1].trending_rank == 2
        assert results[2].trending_rank == 3


@pytest.mark.asyncio
async def test_get_repos_by_language(db):
    """验证按语言筛选."""
    async with db.get_session() as session:
        dao = RepositoryDAO(session)

        await dao.create_or_update(
            {
                "full_name": "org/python-repo",
                "owner": "org",
                "name": "python-repo",
                "language": "Python",
                "total_stars": 500,
            }
        )
        await dao.create_or_update(
            {
                "full_name": "org/go-repo",
                "owner": "org",
                "name": "go-repo",
                "language": "Go",
                "total_stars": 300,
            }
        )
        await dao.create_or_update(
            {
                "full_name": "org/python-repo2",
                "owner": "org",
                "name": "python-repo2",
                "language": "Python",
                "total_stars": 200,
            }
        )

        py_repos = await dao.get_repos_by_language("Python")
        assert len(py_repos) == 2
        assert py_repos[0].full_name == "org/python-repo"  # 按 stars 降序
        assert py_repos[1].full_name == "org/python-repo2"

        go_repos = await dao.get_repos_by_language("Go")
        assert len(go_repos) == 1
        assert go_repos[0].full_name == "org/go-repo"


@pytest.mark.asyncio
async def test_get_repos_without_summary(db):
    """验证获取未摘要项目."""
    async with db.get_session() as session:
        dao = RepositoryDAO(session)

        # 有摘要的
        await dao.create_or_update(
            {
                "full_name": "org/summarized-repo",
                "owner": "org",
                "name": "summarized-repo",
                "readme_summary": "A summary",
            }
        )
        # 无摘要的
        await dao.create_or_update(
            {
                "full_name": "org/unsummarized-repo",
                "owner": "org",
                "name": "unsummarized-repo",
            }
        )
        # 无摘要的 2
        await dao.create_or_update(
            {
                "full_name": "org/unsummarized-repo2",
                "owner": "org",
                "name": "unsummarized-repo2",
            }
        )

        uns = await dao.get_repos_without_summary(limit=10)
        assert len(uns) == 2
        names = {r.full_name for r in uns}
        assert "org/unsummarized-repo" in names
        assert "org/unsummarized-repo2" in names


@pytest.mark.asyncio
async def test_update_summary(db):
    """验证更新摘要信息."""
    async with db.get_session() as session:
        dao = RepositoryDAO(session)
        repo = await dao.create_or_update(
            {
                "full_name": "org/to-summarize",
                "owner": "org",
                "name": "to-summarize",
            }
        )

        await dao.update_summary(
            repo_id=repo.id,  # type: ignore[arg-type]
            summary="This is a summary",
            key_points=["Point 1", "Point 2"],
            tags=["tag1", "tag2"],
        )

        updated = await dao.get_by_full_name("org/to-summarize")
        assert updated.readme_summary == "This is a summary"
        assert updated.key_points == ["Point 1", "Point 2"]
        assert updated.tags == ["tag1", "tag2"]
        assert updated.summarized_at is not None


@pytest.mark.asyncio
async def test_delete_by_full_name(db):
    """验证删除记录."""
    async with db.get_session() as session:
        dao = RepositoryDAO(session)
        await dao.create_or_update(
            {
                "full_name": "org/to-delete",
                "owner": "org",
                "name": "to-delete",
            }
        )

        assert await dao.delete_by_full_name("org/to-delete") is True
        assert await dao.get_by_full_name("org/to-delete") is None

        # 删除不存在的
        assert await dao.delete_by_full_name("org/not-exist") is False


# ── WeeklyReportDAO 测试 ──


@pytest.mark.asyncio
async def test_create_weekly_report(db):
    """验证创建周报记录."""
    week_start = datetime(2025, 1, 6)
    week_end = datetime(2025, 1, 12)

    async with db.get_session() as session:
        dao = WeeklyReportDAO(session)
        report = await dao.create_weekly_report(
            week_start=week_start,
            week_end=week_end,
            language_filter="Python",
            total_repos=25,
            top_repos=[1, 2, 3],
            overview_text="Weekly overview text",
        )

        assert report.id is not None
        assert report.week_start == week_start
        assert report.week_end == week_end
        assert report.language_filter == "Python"
        assert report.total_repos == 25
        assert report.top_repos == [1, 2, 3]
        assert report.overview_text == "Weekly overview text"
        assert report.generated_at is not None
        assert report.published is False


@pytest.mark.asyncio
async def test_get_weekly_report(db):
    """验证按周起始日查询周报."""
    week_start = datetime(2025, 2, 3)
    week_end = datetime(2025, 2, 9)

    async with db.get_session() as session:
        dao = WeeklyReportDAO(session)
        await dao.create_weekly_report(
            week_start=week_start,
            week_end=week_end,
            language_filter=None,
            total_repos=30,
            top_repos=[],
            overview_text="test",
        )

        report = await dao.get_weekly_report(week_start)
        assert report is not None
        assert report.total_repos == 30

        not_found = await dao.get_weekly_report(datetime(2020, 1, 1))
        assert not_found is None


@pytest.mark.asyncio
async def test_list_reports(db):
    """验证列出周报列表."""
    async with db.get_session() as session:
        dao = WeeklyReportDAO(session)

        await dao.create_weekly_report(
            week_start=datetime(2025, 1, 6),
            week_end=datetime(2025, 1, 12),
            language_filter=None,
            total_repos=20,
            top_repos=[],
            overview_text="Week 1",
        )
        await dao.create_weekly_report(
            week_start=datetime(2025, 1, 13),
            week_end=datetime(2025, 1, 19),
            language_filter=None,
            total_repos=30,
            top_repos=[],
            overview_text="Week 2",
        )

        reports = await dao.list_reports(limit=5)
        assert len(reports) == 2
        # 按时间降序，第二周在前
        assert reports[0].overview_text == "Week 2"
        assert reports[1].overview_text == "Week 1"

        # published_only 测试
        published = await dao.list_reports(limit=5, published_only=True)
        assert len(published) == 0


@pytest.mark.asyncio
async def test_mark_published(db):
    """验证标记周报为已发布."""
    async with db.get_session() as session:
        dao = WeeklyReportDAO(session)
        report = await dao.create_weekly_report(
            week_start=datetime(2025, 1, 6),
            week_end=datetime(2025, 1, 12),
            language_filter=None,
            total_repos=20,
            top_repos=[],
            overview_text="test",
        )

        await dao.mark_published(report.id)  # type: ignore[arg-type]

        updated = await dao.get_weekly_report(datetime(2025, 1, 6))
        assert updated.published is True
        assert updated.published_at is not None
