"""测试：Pipeline 流水线编排器。"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from devpulse.services.pipeline import Pipeline


class TestPipeline:
    """Pipeline 流水线单元测试。"""

    @pytest.fixture
    def mock_crawler(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def mock_storage(self) -> MagicMock:
        storage = MagicMock()
        storage.crawl_and_store_trending = AsyncMock()
        storage.summarize_and_update = AsyncMock()
        storage.generate_weekly_report = AsyncMock()
        return storage

    @pytest.fixture
    def pipeline(self, mock_crawler, mock_storage) -> Pipeline:
        return Pipeline(crawler=mock_crawler, storage=mock_storage)

    @pytest.mark.asyncio
    async def test_pipeline_run_success(self, pipeline, mock_storage) -> None:
        """测试四阶段顺利执行。"""
        mock_storage.crawl_and_store_trending.return_value = [
            {"full_name": "test/repo1"},
            {"full_name": "test/repo2"},
        ]
        mock_storage.generate_weekly_report.return_value = MagicMock(id=42)

        result = await pipeline.run_weekly_report(
            language="Python", since="weekly", top_n=10
        )

        assert result["phase1_crawl"] == "成功爬取 2 个项目"
        assert result["phase3_summarize"] == "摘要生成完成"
        assert "42" in result["phase4_report"]
        assert result["errors"] == []
        assert "started_at" in result
        assert "finished_at" in result

        mock_storage.crawl_and_store_trending.assert_awaited_once_with(
            language="Python", since="weekly", limit=10
        )
        mock_storage.summarize_and_update.assert_awaited_once()
        mock_storage.generate_weekly_report.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_pipeline_crawl_failure(self, pipeline, mock_storage) -> None:
        """测试 Phase 1 失败时提前返回。"""
        mock_storage.crawl_and_store_trending.side_effect = RuntimeError("网络错误")

        result = await pipeline.run_weekly_report()

        assert "爬取失败" in result["phase1_crawl"]
        assert "网络错误" in result["phase1_crawl"]
        assert len(result["errors"]) == 1
        assert "Phase 1" in result["errors"][0]
        # Phase 3 不应被调用
        mock_storage.summarize_and_update.assert_not_awaited()
        mock_storage.generate_weekly_report.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_pipeline_summarize_failure_continues(self, pipeline, mock_storage) -> None:
        """测试 Phase 3 失败时 Phase 4 继续执行。"""
        mock_storage.crawl_and_store_trending.return_value = [{"full_name": "test/repo1"}]
        mock_storage.summarize_and_update.side_effect = RuntimeError("LLM 超时")
        mock_storage.generate_weekly_report.return_value = MagicMock(id=7)

        result = await pipeline.run_weekly_report()

        assert result["phase1_crawl"] == "成功爬取 1 个项目"
        assert "摘要失败" in result["phase3_summarize"]
        assert "LLM 超时" in result["phase3_summarize"]
        assert "7" in result["phase4_report"]
        assert len(result["errors"]) == 1
        assert "Phase 3" in result["errors"][0]
        # Phase 4 仍被调用
        mock_storage.generate_weekly_report.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_pipeline_report_structure(self, pipeline, mock_storage) -> None:
        """测试返回结构包含所有必需字段。"""
        mock_storage.crawl_and_store_trending.return_value = []
        mock_storage.generate_weekly_report.return_value = MagicMock(id=0)

        result = await pipeline.run_weekly_report()

        required_keys = [
            "started_at",
            "language",
            "since",
            "phase1_crawl",
            "phase3_summarize",
            "phase4_report",
            "errors",
        ]
        for key in required_keys:
            assert key in result, f"缺少字段: {key}"
