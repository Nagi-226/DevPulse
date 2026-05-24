"""WeeklyReportSummarizer — LLM 摘要 Agent。

负责调用 LLM 生成中文项目摘要和周报总结。
MetaGPT 角色映射：PM + Writer
"""

from __future__ import annotations

import logging
from typing import Any

from devpulse.agents.base import Role

logger = logging.getLogger(__name__)


class WeeklyReportSummarizer(Role):
    """周报摘要生成 Agent。

    对分析后的项目数据调用 LLM 生成中文摘要。
    """

    def __init__(self):
        super().__init__(
            name="WeeklyReportSummarizer",
            profile="产品经理 + 技术作家",
            goal="为每个项目生成中文摘要，并撰写周报导语",
            constraints="摘要需客观准确，不夸大项目价值",
        )

    async def _act(self, analysis_result: dict[str, Any]) -> dict[str, Any]:
        """执行摘要生成。

        Args:
            analysis_result: 分析结果（来自 Analyzer Agent）

        Returns:
            包含项目摘要和周报导语的结果
        """
        repos = analysis_result.get("cleaned_repos", [])
        logger.info(f"[{self.name}] 开始为 {len(repos)} 个项目生成摘要")

        # 模拟摘要 — 后续版本接入真实 LLM
        summarized: list[dict[str, Any]] = []
        for repo in repos:
            summarized.append(
                {
                    **repo,
                    "summary": f"[Mock] {repo.get('name', 'Unknown')} 是一个热门开源项目，"
                    f"本周获得 {repo.get('stars', 0)} 颗星。",
                    "tags": ["mock", "trending", "ai"],
                }
            )

        result: dict[str, Any] = {
            **analysis_result,
            "summarized_repos": summarized,
            "weekly_overview": (
                f"[Mock 周报导语] 本周共有 {len(repos)} 个热门 AI/ML 项目上榜，"
                f"涵盖 {len(analysis_result.get('language_distribution', {}))} 种编程语言。"
            ),
            "summary_notes": "Mock summary — 后续版本接入真实 LLM",
        }

        logger.info(f"[{self.name}] 摘要生成完成")
        return result
