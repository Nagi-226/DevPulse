"""Summarizer 摘要服务单元测试."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from devpulse.services.llm.base import LLMResponse
from devpulse.services.summarizer import Summarizer


def _make_mock_provider(content: str) -> MagicMock:
    """创建 mock LLM Provider."""
    provider = MagicMock()
    provider.generate = AsyncMock(
        return_value=LLMResponse(
            content=content,
            model="test-model",
            usage={"prompt_tokens": 10, "completion_tokens": 5},
        )
    )
    provider.model = "test-model"
    return provider


def _make_repo() -> dict:
    """创建测试用仓库数据."""
    return {
        "full_name": "test-owner/test-repo",
        "description": "A test repository",
        "language": "Python",
        "total_stars": 1000,
        "stars_since": 200,
        "topics": ["testing", "python"],
    }


# ── 单项目摘要 ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_summarize_single_repo():
    """测试单项目摘要生成."""
    mock_provider = _make_mock_provider(
        "概述：一个测试项目，用于演示功能\n"
        "要点：1. 测试框架 2. CI集成 3. 报告生成\n"
        "标签：Python 测试 CI"
    )
    summarizer = Summarizer(mock_provider)
    repo = _make_repo()

    result = await summarizer.summarize_repo(repo)

    assert result["full_name"] == "test-owner/test-repo"
    assert result["summary"] == "一个测试项目，用于演示功能"
    assert result["key_points"] == ["测试框架", "CI集成", "报告生成"]
    assert result["tags"] == ["Python", "测试", "CI"]
    mock_provider.generate.assert_called_once()


# ── 解析测试 ───────────────────────────────────────────

def test_parse_summary_valid():
    """测试解析合法的 LLM 响应."""
    text = (
        "概述：一个AI驱动的测试工具\n"
        "要点：1. 自动生成用例 2. 智能断言 3. 性能分析\n"
        "标签：AI 测试 自动化"
    )
    summarizer = Summarizer(_make_mock_provider(""))
    result = summarizer._parse_summary_response(text)

    assert result["summary"] == "一个AI驱动的测试工具"
    assert result["key_points"] == ["自动生成用例", "智能断言", "性能分析"]
    assert result["tags"] == ["AI", "测试", "自动化"]


def test_parse_summary_malformed():
    """测试解析格式异常的 LLM 响应（鲁棒性）."""
    # 缺少标签
    text_no_tags = "概述：简单项目\n要点：1. 功能A 2. 功能B 3. 功能C\n"
    summarizer = Summarizer(_make_mock_provider(""))
    result = summarizer._parse_summary_response(text_no_tags)
    assert result["summary"] == "简单项目"
    assert len(result["key_points"]) == 3
    assert result["tags"] == []

    # 完全异常文本
    text_broken = "这是随便写的一段话没有结构"
    result = summarizer._parse_summary_response(text_broken)
    assert result["summary"] == ""
    assert result["key_points"] == []
    assert result["tags"] == []

    # 中文冒号
    text_chinese_colon = (
        "概述：混合冒号测试\n"
        "要点：1. 点A 2. 点B 3. 点C\n"
        "标签：标签1 标签2"
    )
    result = summarizer._parse_summary_response(text_chinese_colon)
    assert result["summary"] == "混合冒号测试"
    assert result["key_points"] == ["点A", "点B", "点C"]
    assert result["tags"] == ["标签1", "标签2"]


# ── 批量摘要 ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_batch_summarize():
    """测试批量摘要分组逻辑."""
    mock_provider = _make_mock_provider(
        "概述：项目1概述\n要点：1. P1A 2. P1B 3. P1C\n标签：T1A T1B T1C\n"
        "---\n"
        "概述：项目2概述\n要点：1. P2A 2. P2B 3. P2C\n标签：T2A T2B T2C\n"
        "---\n"
    )
    summarizer = Summarizer(mock_provider, max_batch_size=10)

    repos = [_make_repo(), _make_repo()]
    results = await summarizer.summarize_batch(repos)

    assert len(results) == 2
    assert "summary" in results[0]
    assert "key_points" in results[0]
    assert "tags" in results[0]
    # 验证只调用了一次 API（一个批次）
    assert mock_provider.generate.call_count == 1


@pytest.mark.asyncio
async def test_batch_summarize_empty():
    """测试空列表批量摘要."""
    mock_provider = _make_mock_provider("")
    summarizer = Summarizer(mock_provider)

    results = await summarizer.summarize_batch([])
    assert results == []
    mock_provider.generate.assert_not_called()


@pytest.mark.asyncio
async def test_batch_summarize_multi_batch():
    """测试多批次分批处理."""
    calls = []

    async def mock_generate(system_prompt, user_prompt, **kwargs):
        calls.append(user_prompt)
        count = 3  # 每批 3 个
        parts = "---\n".join(
            f"概述：repo {i}\n要点：1. A{i} 2. B{i} 3. C{i}\n标签：T{i}"
            for i in range(count)
        )
        return LLMResponse(
            content=parts,
            model="test",
            usage={"prompt_tokens": 10, "completion_tokens": 5},
        )

    mock_provider = _make_mock_provider("")
    mock_provider.generate.side_effect = mock_generate
    summarizer = Summarizer(mock_provider, max_batch_size=3)

    repos = [_make_repo() for _ in range(7)]  # 7 个 → 3 批 (3+3+1)
    results = await summarizer.summarize_batch(repos)

    assert len(results) == 7
    assert mock_provider.generate.call_count == 3  # 3 批


# ── 周报 ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_weekly_overview():
    """测试周报导语生成."""
    mock_provider = _make_mock_provider(
        "本周AI/ML领域持续火热，基于LLM的应用框架和Agent工具链成为技术热点，"
        "开发者关注本地化部署和多模态能力。"
    )
    summarizer = Summarizer(mock_provider)

    repos = [
        {**repo, "summary": f"项目 {i} 的摘要"}
        for i, repo in enumerate([_make_repo() for _ in range(5)])
    ]
    overview = await summarizer.generate_weekly_overview(repos)

    assert len(overview) > 0
    assert "LLM" in overview or "AI" in overview
    mock_provider.generate.assert_called_once()


# ── Close ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_summarizer_close():
    """测试 Summarizer 关闭."""
    mock_provider = _make_mock_provider("")
    mock_provider.close = AsyncMock()
    summarizer = Summarizer(mock_provider)

    await summarizer.close()
    mock_provider.close.assert_called_once()
