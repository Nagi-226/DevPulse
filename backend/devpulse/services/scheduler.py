"""定时任务调度模块 — 含 FCM 推送集成."""

from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from devpulse.config import settings
from devpulse.core.database import Database
from devpulse.services.crawler import CrawlerService
from devpulse.services.llm.factory import create_llm_provider
from devpulse.services.pipeline import Pipeline
from devpulse.services.storage import StorageService
from devpulse.services.summarizer import Summarizer

logger = logging.getLogger(__name__)


class DevPulseScheduler:
    """DevPulse 定时任务调度器（含 FCM 推送集成）."""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self._jobs: dict[str, str] = {}

    async def _run_pipeline(self, language: str = "", since: str = "weekly") -> None:
        """执行周报生成流水线 + FCM 推送.

        Args:
            language: 语言过滤.
            since: 时间范围.
        """
        db = Database(
            url=settings.DATABASE_URL,
            echo=settings.DATABASE_ECHO,
        )
        await db.create_tables()

        report_id: int | None = None
        try:
            crawler = CrawlerService()
            provider = create_llm_provider()
            summarizer = Summarizer(provider)
            storage = StorageService(db, crawler, summarizer)
            pipeline = Pipeline(crawler, storage)

            result = await pipeline.run_weekly_report(
                language=language,
                since=since,
            )
            logger.info(
                "定时任务完成: 爬取=%s, 摘要=%s, 周报=%s",
                result.get("phase1_crawl"),
                result.get("phase3_summarize"),
                result.get("phase4_report"),
            )

            # ── FCM 推送（新增）──────────────────
            report_id = result.get("report_id")
            if report_id:
                try:
                    from devpulse.services.fcm_service import fcm_service

                    sent = await fcm_service.send_weekly_report_notification(report_id)
                    logger.info("FCM push sent to %d users for report %d", sent, report_id)
                except Exception:
                    logger.exception("FCM push failed for report %d", report_id)

        except Exception as e:
            logger.error("定时任务执行失败: %s", e)
        finally:
            await provider.close()
            await db.close()

    def add_weekly_job(
        self,
        day_of_week: str = "mon",
        hour: int = 9,
        minute: int = 0,
        language: str = "",
    ) -> None:
        """添加每周定时任务."""
        job_id = f"weekly_report_{language or 'all'}"
        self.scheduler.add_job(
            self._run_pipeline,
            trigger=CronTrigger(
                day_of_week=day_of_week,
                hour=hour,
                minute=minute,
                timezone="Asia/Shanghai",
            ),
            kwargs={"language": language, "since": "weekly"},
            id=job_id,
            name=f"周报生成 ({language or '全语言'}) — 每{day_of_week} {hour:02d}:{minute:02d}",
            replace_existing=True,
        )
        self._jobs[job_id] = f"每{day_of_week} {hour:02d}:{minute:02d}"
        logger.info("已添加定时任务: %s", job_id)

    def add_interval_job(
        self,
        hours: int = 6,
        language: str = "",
        since: str = "daily",
    ) -> None:
        """添加间隔执行任务."""
        job_id = f"interval_fetch_{hours}h_{language or 'all'}"
        self.scheduler.add_job(
            self._run_pipeline,
            trigger=IntervalTrigger(hours=hours, timezone="Asia/Shanghai"),
            kwargs={"language": language, "since": since},
            id=job_id,
            name=f"定时抓取 (每{hours}小时)",
            replace_existing=True,
        )
        self._jobs[job_id] = f"每{hours}小时"
        logger.info("已添加间隔任务: %s", job_id)

    def list_jobs(self) -> list[dict]:
        """列出所有已注册的定时任务."""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": (
                    str(ntr) if (ntr := getattr(job, "next_run_time", None)) else None
                ),
                "trigger": str(job.trigger),
            })
        return jobs

    def remove_job(self, job_id: str) -> bool:
        """移除指定任务."""
        try:
            self.scheduler.remove_job(job_id)
            self._jobs.pop(job_id, None)
            logger.info("已移除定时任务: %s", job_id)
            return True
        except Exception as e:
            logger.error("移除任务失败: %s", e)
            return False

    def start(self) -> None:
        """启动调度器."""
        self.scheduler.start()
        logger.info("调度器已启动，当前 %d 个任务", len(self.scheduler.get_jobs()))

    def shutdown(self) -> None:
        """关闭调度器."""
        self.scheduler.shutdown(wait=False)
        logger.info("调度器已关闭")

    def pause(self) -> None:
        """暂停所有任务."""
        self.scheduler.pause()
        logger.info("调度器已暂停")

    def resume(self) -> None:
        """恢复所有任务."""
        self.scheduler.resume()
        logger.info("调度器已恢复")
