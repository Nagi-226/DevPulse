"""DevPulse Prompt 模板系统 — GitHub Trending 中文摘要."""

from __future__ import annotations

# ── 系统 Prompt（角色定义） ──────────────────────────────

SYSTEM_PROMPT = """你是一个专业的技术趋势分析师，负责为开发者撰写 GitHub Trending 项目的摘要。

要求：
1. 用中文输出
2. 一句话概述（≤40字），说明项目是什么、解决什么问题
3. 核心功能要点（3个，每个≤15字）
4. 适用场景标签（3个关键词）
5. 输出格式严格按模板，不要多余文字"""

# ── 单个项目摘要模板 ────────────────────────────────────

REPO_SUMMARY_TEMPLATE = """请分析以下 GitHub 项目并生成摘要：

项目名称：{full_name}
描述：{description}
语言：{language}
Star 数：{total_stars}（本周新增 {stars_since}）
Topics：{topics}

输出格式：
概述：<一句话>
要点：1. <要点1> 2. <要点2> 3. <要点3>
标签：<标签1> <标签2> <标签3>"""

# ── 周报导语模板 ───────────────────────────────────────

WEEKLY_OVERVIEW_TEMPLATE = (
    "以下是本周 GitHub Trending 的热门项目列表，请生成一个周报导语（≤100字）：\n\n"
    "{repo_list}\n\n"
    "写一段周报导语，概括本周技术趋势和关键词。"
)

# ── 批量摘要模板（节省 API 调用） ──────────────────────────

BATCH_SUMMARY_TEMPLATE = """请为以下 {count} 个 GitHub 项目分别生成摘要，每个项目严格按模板输出。

{repos_text}

输出格式（每项目一组，用 --- 分隔）：
概述：<一句话>
要点：1. <要点1> 2. <要点2> 3. <要点3>
标签：<标签1> <标签2> <标签3>
---"""
