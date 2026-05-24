"""DevPulse MetaGPT Agent 角色定义。

Agent 角色映射：
- Crawler Agent (Engineer) → 数据采集
- Analyzer Agent (Architect) → 清洗分类
- Summarizer Agent (PM + Writer) → LLM 摘要
- Publisher Agent (Engineer) → 周报发布
"""

from devpulse.agents.analyzer_agent import TrendingAnalyzer
from devpulse.agents.base import Message, Role
from devpulse.agents.crawler_agent import GitHubTrendingCrawler
from devpulse.agents.publisher_agent import ReportPublisher
from devpulse.agents.summarizer_agent import WeeklyReportSummarizer

__all__ = [
    "Role",
    "Message",
    "GitHubTrendingCrawler",
    "TrendingAnalyzer",
    "WeeklyReportSummarizer",
    "ReportPublisher",
]
