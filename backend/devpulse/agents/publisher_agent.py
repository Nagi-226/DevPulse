"""ReportPublisher — 周报发布 Agent。

负责生成周报卡片 JSON，写入数据库，推送通知。
MetaGPT 角色映射：Engineer
"""

from __future__ import annotations

import logging
from typing import Any

from devpulse.agents.base import Role

logger = logging.getLogger(__name__)


class ReportPublisher(Role):
    """周报发布 Agent。

    将摘要结果格式化为 API 可消费的周报数据。
    """

    def __init__(self):
        super().__init__(
            name="ReportPublisher",
            profile="发布工程师",
            goal="生成周报卡片 JSON，写入数据库，推送通知",
            constraints="确保数据格式符合 API 规范",
        )

    async def _act(self, summary_result: dict[str, Any]) -> dict[str, Any]:
        """执行周报发布。

        Args:
            summary_result: 摘要结果（来自 Summarizer Agent）

        Returns:
            发布结果，包含周报 ID 和状态
        """
        repos = summary_result.get("summarized_repos", [])
        logger.info(f"[{self.name}] 开始发布周报，包含 {len(repos)} 个项目")

        # 模拟发布 — 后续版本接入真实数据库和通知
        result: dict[str, Any] = {
            "report_id": "mock-weekly-2026-W21",
            "status": "published",
            "total_repos": len(repos),
            "overview": summary_result.get("weekly_overview", ""),
            "repos": repos,
            "publish_notes": "Mock publish — 后续版本接入真实数据库和通知",
        }

        logger.info(f"[{self.name}] 周报发布完成: {result['report_id']}")
        return result
