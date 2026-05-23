"""DevPulse CLI — 命令行工具入口。

用法:
    python -m devpulse.cli.main fetch [--language Python] [--since weekly]
    python -m devpulse.cli.main report --week 2026-W21
    python -m devpulse.cli.main serve
    python -m devpulse.cli.main status
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys


def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器。

    Returns:
        配置好的 ArgumentParser 实例。
    """
    parser = argparse.ArgumentParser(
        prog="devpulse",
        description="DevPulse - GitHub Trending AI/ML 项目周报工具",
    )
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # fetch — 抓取并处理
    fetch_parser = subparsers.add_parser("fetch", help="抓取 GitHub Trending 并生成周报")
    fetch_parser.add_argument("--language", "-l", default="", help="按语言过滤 (如 Python)")
    fetch_parser.add_argument(
        "--since", "-s", default="weekly", choices=["daily", "weekly", "monthly"]
    )
    fetch_parser.add_argument("--top-n", "-n", type=int, default=25, help="处理前 N 个项目")
    fetch_parser.add_argument("--no-summarize", action="store_true", help="跳过 LLM 摘要")

    # report — 查看周报
    report_parser = subparsers.add_parser("report", help="查看历史周报")
    report_parser.add_argument("--limit", "-n", type=int, default=10, help="显示数量")
    report_parser.add_argument("--week", "-w", default="", help="指定周 (格式: 2026-W21)")

    # serve — 启动 API 服务
    serve_parser = subparsers.add_parser("serve", help="启动 FastAPI 服务")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", "-p", type=int, default=8000)

    # status — 查看系统状态
    subparsers.add_parser("status", help="查看系统状态（数据库连接、LLM Provider 等）")

    return parser


async def handle_fetch(args: argparse.Namespace) -> None:
    """处理 fetch 命令。

    Args:
        args: 解析后的命令行参数。
    """
    from devpulse.config import settings
    from devpulse.core.database import Database
    from devpulse.services.crawler import CrawlerService
    from devpulse.services.llm.factory import create_llm_provider
    from devpulse.services.pipeline import Pipeline
    from devpulse.services.storage import StorageService
    from devpulse.services.summarizer import Summarizer

    db = Database(url=settings.DATABASE_URL, echo=settings.DATABASE_ECHO)
    await db.create_tables()

    try:
        crawler = CrawlerService()
        provider = create_llm_provider()
        summarizer = Summarizer(provider)
        storage = StorageService(db, crawler, summarizer)
        pipeline = Pipeline(crawler, storage)

        result = await pipeline.run_weekly_report(
            language=args.language,
            since=args.since,
            top_n=args.top_n,
        )

        print("\n" + "=" * 50)
        print("DevPulse 周报生成流水线")
        print("=" * 50)
        print(f"开始时间: {result['started_at']}")
        print(f"语言过滤: {result['language'] or '全语言'}")
        print(f"时间范围: {result['since']}")
        print("-" * 50)
        print(f"Phase 1+2 (爬取+存储): {result['phase1_crawl']}")
        print(f"Phase 3 (LLM摘要):    {result['phase3_summarize']}")
        print(f"Phase 4 (周报生成):   {result['phase4_report']}")
        if result["errors"]:
            print(f"错误: {len(result['errors'])} 个")
            for err in result["errors"]:
                print(f"  - {err}")
        print(f"完成时间: {result['finished_at']}")
        print("=" * 50)
    except Exception as e:
        print(f"流水线执行失败: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        await provider.close()
        await db.close()


async def handle_report(args: argparse.Namespace) -> None:
    """处理 report 命令。

    Args:
        args: 解析后的命令行参数。
    """
    import datetime

    from devpulse.config import settings
    from devpulse.core.database import Database
    from devpulse.core.repository import WeeklyReportDAO

    db = Database(url=settings.DATABASE_URL, echo=False)
    await db.create_tables()

    try:
        async with db.get_session() as session:
            dao = WeeklyReportDAO(session)

            if args.week:
                # 解析 2026-W21 格式
                year, week = args.week.split("-W")
                week_start = datetime.datetime.fromisocalendar(int(year), int(week), 1)
                report = await dao.get_weekly_report(week_start)
                if report:
                    print(f"周报: {report.week_start.date()} ~ {report.week_end.date()}")
                    print(f"项目数: {report.total_repos}")
                    print(f"导语: {report.overview_text}")
                else:
                    print(f"未找到 {args.week} 的周报")
            else:
                reports = await dao.list_reports(limit=args.limit)
                print(f"{'周起始':<12} {'项目数':<8} {'已发布':<6}")
                print("-" * 30)
                for r in reports:
                    published = "是" if r.published else "否"
                    print(f"{str(r.week_start.date()):<12} {r.total_repos:<8} {published:<6}")
    finally:
        await db.close()


async def handle_serve(args: argparse.Namespace) -> None:
    """处理 serve 命令。

    Args:
        args: 解析后的命令行参数。
    """
    import uvicorn

    uvicorn.run(
        "devpulse.main:app",
        host=args.host,
        port=args.port,
        reload=True,
    )


async def handle_status(args: argparse.Namespace) -> None:
    """处理 status 命令，检查各组件连通性。

    Args:
        args: 解析后的命令行参数。
    """
    import sqlalchemy

    from devpulse.config import settings
    from devpulse.core.database import Database

    print("DevPulse 系统状态检查")
    print("=" * 40)
    print(f"LLM Provider: {settings.LLM_PROVIDER}")
    print(f"Database URL:  {settings.DATABASE_URL[:50]}...")
    print(f"OpenAI Key:    {'已配置' if settings.OPENAI_API_KEY else '未配置'}")
    print(f"Anthropic Key: {'已配置' if settings.ANTHROPIC_API_KEY else '未配置'}")

    # 数据库连接测试
    db = Database(url=settings.DATABASE_URL, echo=False)
    try:
        await db.create_tables()
        async with db.get_session() as session:
            result = await session.execute(sqlalchemy.text("SELECT 1"))
            result.fetchone()
        print("Database:      ✅ 连接正常")
    except Exception as e:
        print(f"Database:      ❌ 连接失败 ({e})")
    finally:
        await db.close()


def main() -> None:
    """CLI 入口函数。"""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    if args.command == "fetch":
        asyncio.run(handle_fetch(args))
    elif args.command == "report":
        asyncio.run(handle_report(args))
    elif args.command == "serve":
        asyncio.run(handle_serve(args))
    elif args.command == "status":
        asyncio.run(handle_status(args))


if __name__ == "__main__":
    main()
