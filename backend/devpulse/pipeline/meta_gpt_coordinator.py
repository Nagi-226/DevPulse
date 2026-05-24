"""MetaGPTCoordinator — MetaGPT 多 Agent 流水线协调器。

编排 Crawler → Analyzer → Summarizer → Publisher 四阶段流水线。
"""

from __future__ import annotations

import logging
from typing import Any

from devpulse.agents.analyzer_agent import TrendingAnalyzer
from devpulse.agents.crawler_agent import GitHubTrendingCrawler
from devpulse.agents.publisher_agent import ReportPublisher
from devpulse.agents.summarizer_agent import WeeklyReportSummarizer

logger = logging.getLogger(__name__)


class MetaGPTCoordinator:
    """MetaGPT 多 Agent 流水线协调器。

    按 SOP 顺序链式调用四个 Agent：
    Crawler → Analyzer → Summarizer → Publisher
    """

    def __init__(self):
        """初始化四个 Agent 实例。"""
        self.crawler = GitHubTrendingCrawler()
        self.analyzer = TrendingAnalyzer()
        self.summarizer = WeeklyReportSummarizer()
        self.publisher = ReportPublisher()

        logger.info("MetaGPTCoordinator 初始化完成，4 个 Agent 就绪")

    async def run(
        self,
        language: str = "",
        since: str = "weekly",
        top_n: int = 25,
    ) -> dict[str, Any]:
        """执行完整 MetaGPT 流水线。

        Args:
            language: 编程语言过滤
            since: 时间范围（daily/weekly/monthly）
            top_n: 返回前 N 个项目

        Returns:
            流水线执行结果汇总
        """
        logger.info("=" * 50)
        logger.info("MetaGPT 流水线启动")
        logger.info(f"参数: language={language or 'all'}, since={since}, top_n={top_n}")
        logger.info("=" * 50)

        # Phase 1: Crawler
        logger.info("[Phase 1/4] Crawler Agent 启动...")
        repos = await self.crawler.run(language=language, since=since, top_n=top_n)
        logger.info(f"[Phase 1/4] Crawler Agent 完成: {len(repos)} 个项目")

        # Phase 2: Analyzer
        logger.info("[Phase 2/4] Analyzer Agent 启动...")
        analysis = await self.analyzer.run(repos)
        logger.info(
            f"[Phase 2/4] Analyzer Agent 完成: "
            f"{analysis.get('total_repos', 0)} 个项目, "
            f"{analysis.get('total_stars', 0)} 总星数"
        )

        # Phase 3: Summarizer
        logger.info("[Phase 3/4] Summarizer Agent 启动...")
        summary = await self.summarizer.run(analysis)
        logger.info(
            f"[Phase 3/4] Summarizer Agent 完成: "
            f"{len(summary.get('summarized_repos', []))} 个摘要"
        )

        # Phase 4: Publisher
        logger.info("[Phase 4/4] Publisher Agent 启动...")
        report = await self.publisher.run(summary)
        logger.info(
            f"[Phase 4/4] Publisher Agent 完成: " f"report_id={report.get('report_id', 'N/A')}"
        )

        logger.info("=" * 50)
        logger.info("MetaGPT 流水线完成")
        logger.info("=" * 50)

        return {
            "pipeline": "MetaGPT",
            "phases": {
                "crawler": f"{len(repos)} repos",
                "analyzer": (
                    f"{analysis.get('total_repos', 0)} repos, "
                    f"{analysis.get('total_stars', 0)} stars"
                ),
                "summarizer": f"{len(summary.get('summarized_repos', []))} summaries",
                "publisher": f"report_id={report.get('report_id', 'N/A')}",
            },
            "report": report,
            "agent_memory": {
                "crawler": self.crawler.get_memory_summary(),
                "analyzer": self.analyzer.get_memory_summary(),
                "summarizer": self.summarizer.get_memory_summary(),
                "publisher": self.publisher.get_memory_summary(),
            },
        }
