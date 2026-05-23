"""ORM 数据模型单元测试."""

from datetime import datetime

from devpulse.core.models import Repository, WeeklyReport


def test_repository_model_fields():
    """验证 Repository 模型的字段类型和默认值."""
    now = datetime.now()
    repo = Repository(
        full_name="microsoft/codegraph",
        owner="microsoft",
        name="codegraph",
        description="Code graph analysis tool",
        language="Python",
        topics=["code-analysis", "graph"],
        total_stars=1000,
        stars_since=50,
        forks=200,
        forks_since=10,
        open_issues=5,
        created_at=now,
        updated_at=now,
        url="https://github.com/microsoft/codegraph",
        has_readme=True,
        readme_content="# Codegraph\nA tool for code analysis",
        readme_summary="Code analysis tool",
        key_points=["Static analysis", "Graph visualization"],
        tags=["analysis", "visualization"],
        crawled_at=now,
        summarized_at=now,
        trending_rank=1,
        trending_since="weekly",
    )

    assert repo.id is None  # 未持久化
    assert repo.full_name == "microsoft/codegraph"
    assert repo.owner == "microsoft"
    assert repo.name == "codegraph"
    assert repo.description == "Code graph analysis tool"
    assert repo.language == "Python"
    assert repo.topics == ["code-analysis", "graph"]
    assert repo.total_stars == 1000
    assert repo.stars_since == 50
    assert repo.forks == 200
    assert repo.forks_since == 10
    assert repo.open_issues == 5
    assert repo.created_at == now
    assert repo.updated_at == now
    assert repo.url == "https://github.com/microsoft/codegraph"
    assert repo.has_readme is True
    assert repo.readme_content == "# Codegraph\nA tool for code analysis"
    assert repo.readme_summary == "Code analysis tool"
    assert repo.key_points == ["Static analysis", "Graph visualization"]
    assert repo.tags == ["analysis", "visualization"]
    assert repo.crawled_at == now
    assert repo.summarized_at == now
    assert repo.trending_rank == 1
    assert repo.trending_since == "weekly"

    # 测试 optional 字段默认值
    repo2 = Repository(full_name="test/repo", owner="test", name="repo")
    assert repo2.description is None
    assert repo2.language is None
    assert repo2.topics is None
    assert repo2.readme_content is None
    assert repo2.readme_summary is None
    assert repo2.key_points is None
    assert repo2.tags is None
    assert repo2.crawled_at is None
    assert repo2.summarized_at is None
    assert repo2.trending_rank is None
    assert repo2.trending_since is None

    # 测试 __repr__
    assert "Repository" in repr(repo)
    assert "microsoft/codegraph" in repr(repo)


def test_weekly_report_model():
    """验证 WeeklyReport 模型的字段类型和默认值."""
    now = datetime.now()
    week_start = datetime(2025, 1, 1)
    week_end = datetime(2025, 1, 8)

    report = WeeklyReport(
        week_start=week_start,
        week_end=week_end,
        language_filter="Python",
        total_repos=25,
        top_repos=[1, 2, 3, 4, 5],
        overview_text="This week's AI/ML trends...",
        generated_at=now,
        published=True,
        published_at=now,
    )

    assert report.id is None
    assert report.week_start == week_start
    assert report.week_end == week_end
    assert report.language_filter == "Python"
    assert report.total_repos == 25
    assert report.top_repos == [1, 2, 3, 4, 5]
    assert report.overview_text == "This week's AI/ML trends..."
    assert report.generated_at == now
    assert report.published is True
    assert report.published_at == now

    # 测试 optional 字段默认值
    report2 = WeeklyReport(
        week_start=week_start,
        week_end=week_end,
    )
    assert report2.language_filter is None
    assert report2.top_repos is None
    assert report2.overview_text is None
    assert report2.generated_at is None
    assert report2.published_at is None

    # 测试 __repr__
    assert "WeeklyReport" in repr(report)
    assert "2025-01-01" in repr(report)
