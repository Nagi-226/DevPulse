"""DevPulse 周报生成流水线编排。

爬虫 → 存储 → 摘要 → 周报 四阶段异步流水线。
支持原生流水线（默认）和 MetaGPT 多 Agent 流水线（通过 META_GPT_ENABLED 开关切换）。
"""

import logging
from datetime import datetime, timedelta
from typing import Any

from devpulse.config import settings
from devpulse.services.crawler import CrawlerService
from devpulse.services.storage import StorageService

logger = logging.getLogger(__name__)


class Pipeline:
    """周报生成流水线编排器。

    整合爬虫、存储、摘要三个阶段，提供一键式周报生成入口。
    当 META_GPT_ENABLED=True 时，自动切换为 MetaGPT 多 Agent 流水线。
    """

    def __init__(
        self,
        crawler: CrawlerService,
        storage: StorageService,
    ):
        self.crawler = crawler
        self.storage = storage
        self._meta_gpt_coordinator = None

    async def run_weekly_report(
        self,
        language: str = "",
        since: str = "weekly",
        top_n: int = 25,
    ) -> dict[str, Any]:
        """执行完整周报生成流水线。

        根据 META_GPT_ENABLED 开关选择执行路径：
        - False（默认）：原生流水线（爬虫 → 存储 → 摘要 → 周报）
        - True：MetaGPT 多 Agent 流水线（Crawler → Analyzer → Summarizer → Publisher）

        Returns:
            dict: 包含各阶段结果的汇总信息
        """
        if settings.META_GPT_ENABLED:
            return await self._run_meta_gpt_pipeline(language=language, since=since, top_n=top_n)
        return await self._run_native_pipeline(language=language, since=since, top_n=top_n)

    async def _run_native_pipeline(
        self,
        language: str = "",
        since: str = "weekly",
        top_n: int = 25,
    ) -> dict[str, Any]:
        """原生流水线：爬虫 → 存储 → 摘要 → 周报。

        Phase 1: 爬取 GitHub Trending
        Phase 2: 存储到数据库
        Phase 3: LLM 摘要生成
        Phase 4: 生成周报总结
        """
        report = {
            "pipeline": "Native",
            "started_at": datetime.utcnow().isoformat(),
            "language": language,
            "since": since,
            "phase1_crawl": None,
            "phase2_store": None,
            "phase3_summarize": None,
            "phase4_report": None,
            "errors": [],
        }

        # Phase 1+2: 爬取并存储
        logger.info("Phase 1+2: 爬取并存储 Trending 数据...")
        try:
            repos = await self.storage.crawl_and_store_trending(
                language=language, since=since, limit=top_n
            )
            report["phase1_crawl"] = f"成功爬取 {len(repos)} 个项目"
            logger.info(report["phase1_crawl"])
        except Exception as e:
            report["phase1_crawl"] = f"爬取失败: {e}"
            report["errors"].append(f"Phase 1: {e}")
            logger.error(report["phase1_crawl"])
            return report

        # Phase 3: LLM 摘要
        logger.info("Phase 3: LLM 摘要生成...")
        try:
            await self.storage.summarize_and_update()
            report["phase3_summarize"] = "摘要生成完成"
            logger.info(report["phase3_summarize"])
        except Exception as e:
            report["phase3_summarize"] = f"摘要失败: {e}"
            report["errors"].append(f"Phase 3: {e}")
            logger.error(report["phase3_summarize"])

        # Phase 4: 周报
        logger.info("Phase 4: 周报生成...")
        try:
            week_start = datetime.utcnow().replace(
                hour=0, minute=0, second=0, microsecond=0
            ) - timedelta(days=datetime.utcnow().weekday())
            weekly = await self.storage.generate_weekly_report(
                week_start=week_start,
                language_filter=language or None,
            )
            wid = weekly.id if hasattr(weekly, "id") else "N/A"
            report["phase4_report"] = f"周报已生成 (ID: {wid})"
            logger.info(report["phase4_report"])
        except Exception as e:
            report["phase4_report"] = f"周报生成失败: {e}"
            report["errors"].append(f"Phase 4: {e}")
            logger.error(report["phase4_report"])

        report["finished_at"] = datetime.utcnow().isoformat()
        return report

    async def _run_meta_gpt_pipeline(
        self,
        language: str = "",
        since: str = "weekly",
        top_n: int = 25,
    ) -> dict[str, Any]:
        """MetaGPT 多 Agent 流水线。

        Crawler Agent → Analyzer Agent → Summarizer Agent → Publisher Agent
        """
        from devpulse.pipeline.meta_gpt_coordinator import MetaGPTCoordinator

        if self._meta_gpt_coordinator is None:
            self._meta_gpt_coordinator = MetaGPTCoordinator()

        logger.info("使用 MetaGPT 多 Agent 流水线")
        result = await self._meta_gpt_coordinator.run(language=language, since=since, top_n=top_n)

        # 转换为统一格式
        return {
            "pipeline": "MetaGPT",
            "started_at": datetime.utcnow().isoformat(),
            "language": language,
            "since": since,
            "phase1_crawl": f"MetaGPT: {result['phases']['crawler']}",
            "phase2_store": f"MetaGPT: {result['phases']['analyzer']}",
            "phase3_summarize": f"MetaGPT: {result['phases']['summarizer']}",
            "phase4_report": f"MetaGPT: {result['phases']['publisher']}",
            "errors": [],
            "finished_at": datetime.utcnow().isoformat(),
        }
