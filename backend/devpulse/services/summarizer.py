"""GitHub Trending 项目摘要服务 — 含置信度评分."""

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
        """为单个仓库生成摘要（含置信度评分）.

        Args:
            repo: 仓库信息字典，必须包含 full_name, description, language,
                  total_stars, stars_since, topics.

        Returns:
            原 repo 字典基础上增加 summary, key_points, tags, confidence_score,
            review_required 字段.
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
        confidence = self._calculate_confidence(parsed)
        return {
            **repo,
            "summary": parsed.get("summary", ""),
            "key_points": parsed.get("key_points", []),
            "tags": parsed.get("tags", []),
            "confidence_score": confidence["score"],
            "review_required": confidence["review_required"],
        }

    async def summarize_batch(self, repos: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """批量生成摘要，减少 API 调用.

        Args:
            repos: 仓库信息列表.

        Returns:
            每个仓库增加摘要字段 + confidence_score + review_required 的列表.
        """
        if not repos:
            return []

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
            for repo in repos[:10]
        )

        prompt = WEEKLY_OVERVIEW_TEMPLATE.format(repo_list=repo_list)

        response = await self._provider.generate(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=prompt,
            max_tokens=150,
            temperature=0.3,
        )

        return response.content.strip()

    def _calculate_confidence(self, parsed: dict[str, Any]) -> dict[str, Any]:
        """计算 LLM 摘要置信度评分 (0.0-1.0).

        评估维度:
            1. keyword_coverage (0.4): 是否有 summary/key_points/tags
            2. summary_length (0.3): 摘要长度是否合理 (≥30 chars)
            3. sentence_completeness (0.15): 是否以句号/问号/感叹号结尾
            4. language_consistency (0.15): 摘要语言一致性

        Args:
            parsed: _parse_summary_response 的输出.

        Returns:
            {score: float, review_required: bool, breakdown: {...}}
        """
        summary = parsed.get("summary", "")
        key_points = parsed.get("key_points", [])
        tags = parsed.get("tags", [])

        # 1. 关键词覆盖度 (40%)
        kw_score = 0.0
        if summary:
            kw_score += 0.5
        if key_points and len(key_points) > 0:
            kw_score += 0.3
        if tags and len(tags) > 0:
            kw_score += 0.2

        # 2. 摘要长度 (30%)
        length_score = 0.0
        if len(summary) >= 100:
            length_score = 1.0
        elif len(summary) >= 50:
            length_score = 0.7
        elif len(summary) >= 30:
            length_score = 0.4
        elif len(summary) >= 10:
            length_score = 0.2

        # 3. 句式完整性 (15%)
        completeness_score = 0.0
        if summary and summary.strip()[-1] in ("。", ".", "！", "!", "？", "?"):
            completeness_score = 1.0
        elif summary and len(summary) >= 20:
            completeness_score = 0.5

        # 4. 语言一致性 (15%)
        lang_score = 0.0
        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", summary))
        total_chars = len(summary.replace(" ", ""))
        if total_chars > 0:
            ratio = chinese_chars / total_chars if total_chars > 0 else 0
            # 纯中文或纯英文都是好的，混合可能有问题
            if ratio > 0.8 or ratio < 0.2:
                lang_score = 1.0
            elif ratio > 0.5:
                lang_score = 0.6
            else:
                lang_score = 0.4
        elif summary:
            lang_score = 0.5

        score = round(
            kw_score * 0.4
            + length_score * 0.3
            + completeness_score * 0.15
            + lang_score * 0.15,
            4,
        )
        score = max(0.0, min(1.0, score))

        # 阈值默认 0.7
        threshold = 0.7
        review_required = score < threshold

        return {
            "score": score,
            "review_required": review_required,
            "breakdown": {
                "keyword_coverage": round(kw_score, 4),
                "summary_length": round(length_score, 4),
                "sentence_completeness": round(completeness_score, 4),
                "language_consistency": round(lang_score, 4),
            },
        }

    def _parse_summary_response(self, text: str) -> dict[str, Any]:
        """解析 LLM 返回的结构化文本.

        处理格式异常，使用正则或简单规则提取字段.
        """
        text = re.sub(r"\n+", "\n", text.strip())

        summary_match = re.search(r"概述[:：]\s*(.+)", text)
        summary = summary_match.group(1).strip() if summary_match else ""

        points_match = re.search(r"要点[:：]\s*(.+)", text)
        key_points = []
        if points_match:
            points_text = points_match.group(1)
            point_items = re.findall(r"\d+\.\s*(.+?)(?=\s*\d+\.\s|$)", points_text)
            key_points = [p.strip() for p in point_items[:3]]

        tags_match = re.search(r"标签[:：]\s*(.+)", text)
        tags = []
        if tags_match:
            tags_text = tags_match.group(1)
            tags = re.split(r"[,\s]+", tags_text.strip())
            tags = [t for t in tags if t and len(t) < 20][:3]

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
            max_tokens=len(batch) * 200 + 100,
            temperature=0.3,
        )

        parts = response.content.split("---")
        results = []
        for repo, part in zip(batch, parts, strict=False):
            parsed = self._parse_summary_response(part)
            confidence = self._calculate_confidence(parsed)
            results.append(
                {
                    **repo,
                    "summary": parsed.get("summary", ""),
                    "key_points": parsed.get("key_points", []),
                    "tags": parsed.get("tags", []),
                    "confidence_score": confidence["score"],
                    "review_required": confidence["review_required"],
                }
            )

        return results

    async def close(self) -> None:
        """关闭底层 LLM Provider."""
        await self._provider.close()
