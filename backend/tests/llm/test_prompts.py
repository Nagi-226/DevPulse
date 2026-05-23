"""Prompt 模板单元测试."""

from __future__ import annotations

from devpulse.services.llm.prompts import (
    BATCH_SUMMARY_TEMPLATE,
    REPO_SUMMARY_TEMPLATE,
    SYSTEM_PROMPT,
    WEEKLY_OVERVIEW_TEMPLATE,
)


def test_system_prompt_exists():
    """验证系统 Prompt 非空."""
    assert len(SYSTEM_PROMPT) > 50
    assert "技术趋势" in SYSTEM_PROMPT


def test_repo_summary_template_format():
    """测试单个项目摘要模板格式化."""
    repo = {
        "full_name": "owner/repo",
        "description": "A simple test",
        "language": "Python",
        "total_stars": 500,
        "stars_since": 50,
        "topics": ["testing", "ai"],
    }

    result = REPO_SUMMARY_TEMPLATE.format(
        full_name=repo["full_name"],
        description=repo["description"],
        language=repo["language"],
        total_stars=repo["total_stars"],
        stars_since=repo["stars_since"],
        topics=", ".join(repo["topics"]),
    )

    assert "owner/repo" in result
    assert "A simple test" in result
    assert "Python" in result
    assert "500" in result
    assert "50" in result
    assert "testing, ai" in result
    assert "概述" in result
    assert "要点" in result
    assert "标签" in result


def test_batch_template_contains_all_repos():
    """测试批量模板包含所有项目."""
    repos_text = "项目1详情\n\n项目2详情\n\n项目3详情"
    result = BATCH_SUMMARY_TEMPLATE.format(count=3, repos_text=repos_text)

    assert "3" in result
    assert "项目1详情" in result
    assert "项目2详情" in result
    assert "项目3详情" in result
    assert "---" in result  # 分隔符说明


def test_batch_template_with_single_repo():
    """测试批量模板单个项目格式化."""
    repos_text = "单个项目"
    result = BATCH_SUMMARY_TEMPLATE.format(count=1, repos_text=repos_text)

    assert "1" in result
    assert "单个项目" in result


def test_weekly_overview_template():
    """测试周报模板格式化."""
    repo_list = "- owner/a: 摘要A...\n- owner/b: 摘要B..."
    result = WEEKLY_OVERVIEW_TEMPLATE.format(repo_list=repo_list)

    assert "周报导语" in result
    assert "owner/a" in result
    assert "owner/b" in result
    assert "100字" in result
