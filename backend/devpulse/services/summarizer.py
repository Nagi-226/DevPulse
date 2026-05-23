"""GitHub Trending 项目摘要服务."""

from __future__ import annotations

import logging
import re
from typing import Any

from devpulse.services.llm.base import BaseLLMProvider
from devpulse.services.llm.prompts import (
    BATCH_SUMMARY_TEMPLATE,
    REPO_SUMMARY_TEMPLATE,
    SYSTEM_PROMPT,
    WEEKLY_OVERVIEW_TEMPLATE,
)

logger = logging.getLogger(__name__)


class Summarizer:
    """使用 LLM 生成 GitHub 项目摘要的服务.

    Args:
        provider: LLM Provider 实例.
        max_batch_size: 批量摘要时每批最大项目数，默认 10.
    """

    def __init__(self, provider: BaseLLMProvider, max_batch_size: int = 10) -> None:
        self._provider = provider
        self._max_batch_size = max_batch_size

    async def summarize_repo(self, repo: dict[str, Any]) -> dict[str, Any]:
        """为单个仓库生成摘要.

        Args:
            repo: 仓库信息字典，必须包含 full_name, description, language,
                  total_stars, stars_since, topics.

        Returns:
            原 repo 字典基础上增加 summary, key_points, tags 字段.
        """
        prompt = REPO_SUMMARY_TEMPLATE.format(
            full_name=repo.get("full_name", ""),
            description=repo.get("description", ""),
            language=repo.get("language", ""),
            total_stars=repo.get("total_stars", 0),
            stars_since=repo.get("stars_since", 0),
            topics=", ".join(repo.get("topics", [])),
        )

        response = await self._provider.generate(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=prompt,
            max_tokens=500,
            temperature=0.3,
        )

        parsed = self._parse_summary_response(response.content)
        return {
            **repo,
            "summary": parsed.get("summary", ""),
            "key_points": parsed.get("key_points", []),
            "tags": parsed.get("tags", []),
        }

    async def summarize_batch(self, repos: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """批量生成摘要，减少 API 调用.

        Args:
            repos: 仓库信息列表.

        Returns:
            每个仓库增加摘要字段的列表，顺序与输入一致.
        """
        if not repos:
            return []

        # 分批处理
        batches = [
            repos[i : i + self._max_batch_size]
            for i in range(0, len(repos), self._max_batch_size)
        ]

        results: list[dict[str, Any]] = []
        for batch in batches:
            batch_results = await self._summarize_single_batch(batch)
            results.extend(batch_results)

        return results

    async def generate_weekly_overview(self, repos: list[dict[str, Any]]) -> str:
        """生成周报导语（趋势总结）.

        Args:
            repos: 已生成摘要的仓库列表.

        Returns:
            ≤100 字的周报导语.
        """
        repo_list = "\n".join(
            f"- {repo.get('full_name', '')}: {repo.get('summary', '')[:50]}..."
            for repo in repos[:10]  # 最多取 10 个
        )

        prompt = WEEKLY_OVERVIEW_TEMPLATE.format(repo_list=repo_list)

        response = await self._provider.generate(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=prompt,
            max_tokens=150,
            temperature=0.3,
        )

        return response.content.strip()

    def _parse_summary_response(self, text: str) -> dict[str, Any]:
        """解析 LLM 返回的结构化文本.

        处理格式异常，使用正则或简单规则提取字段.
        """
        # 清理多余空格和换行
        text = re.sub(r"\n+", "\n", text.strip())

        # 提取概述
        summary_match = re.search(r"概述[:：]\s*(.+)", text)
        summary = summary_match.group(1).strip() if summary_match else ""

        # 提取要点
        points_match = re.search(r"要点[:：]\s*(.+)", text)
        key_points = []
        if points_match:
            points_text = points_match.group(1)
            # 匹配 1. xxx 2. yyy 3. zzz 格式
            point_items = re.findall(r"\d+\.\s*(.+?)(?=\s*\d+\.\s|$)", points_text)
            key_points = [p.strip() for p in point_items[:3]]

        # 提取标签
        tags_match = re.search(r"标签[:：]\s*(.+)", text)
        tags = []
        if tags_match:
            tags_text = tags_match.group(1)
            # 匹配空格或逗号分隔的标签
            tags = re.split(r"[,\s]+", tags_text.strip())
            tags = [t for t in tags if t and len(t) < 20][:3]  # 过滤空值，限制长度

        return {
            "summary": summary,
            "key_points": key_points,
            "tags": tags,
        }

    async def _summarize_single_batch(self, batch: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """处理单个批次（最多 max_batch_size 个项目）."""
        repos_text = "\n\n".join(
            REPO_SUMMARY_TEMPLATE.format(
                full_name=repo.get("full_name", ""),
                description=repo.get("description", ""),
                language=repo.get("language", ""),
                total_stars=repo.get("total_stars", 0),
                stars_since=repo.get("stars_since", 0),
                topics=", ".join(repo.get("topics", [])),
            )
            for repo in batch
        )

        prompt = BATCH_SUMMARY_TEMPLATE.format(
            count=len(batch),
            repos_text=repos_text,
        )

        response = await self._provider.generate(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=prompt,
            max_tokens=len(batch) * 200 + 100,  # 动态调整 token
            temperature=0.3,
        )

        # 按 --- 分隔每个项目的响应
        parts = response.content.split("---")
        results = []
        for repo, part in zip(batch, parts, strict=False):
            parsed = self._parse_summary_response(part)
            results.append(
                {
                    **repo,
                    "summary": parsed.get("summary", ""),
                    "key_points": parsed.get("key_points", []),
                    "tags": parsed.get("tags", []),
                }
            )

        return results

    async def close(self) -> None:
        """关闭底层 LLM Provider."""
        await self._provider.close()
