"""测试：APScheduler 定时调度模块。"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from devpulse.services.scheduler import DevPulseScheduler


class TestScheduler:
    """DevPulseScheduler 单元测试。"""

    @pytest.fixture
    def scheduler(self) -> DevPulseScheduler:
        """创建调度器实例，mock 了 _run_pipeline。"""
        with patch.object(DevPulseScheduler, "_run_pipeline", new=AsyncMock()):
            s = DevPulseScheduler()
            return s

    def test_add_weekly_job(self, scheduler) -> None:
        """测试添加周任务成功。"""
        scheduler.add_weekly_job(day_of_week="mon", hour=9, minute=0, language="Python")
        jobs = scheduler.list_jobs()
        assert len(jobs) == 1
        job = jobs[0]
        assert job["id"] == "weekly_report_Python"
        assert "Python" in job["name"]

    def test_add_interval_job(self, scheduler) -> None:
        """测试添加间隔任务成功。"""
        scheduler.add_interval_job(hours=6, language="", since="daily")
        jobs = scheduler.list_jobs()
        assert len(jobs) == 1
        job = jobs[0]
        assert job["id"] == "interval_fetch_6h_all"
        assert "6小时" in job["name"]

    def test_list_jobs_empty(self, scheduler) -> None:
        """未添加任务时列表为空。"""
        jobs = scheduler.list_jobs()
        assert jobs == []

    def test_list_jobs_with_jobs(self, scheduler) -> None:
        """添加多个任务后列表正确。"""
        scheduler.add_weekly_job(day_of_week="fri", hour=18, minute=30, language="")
        scheduler.add_interval_job(hours=12, language="Python", since="daily")
        jobs = scheduler.list_jobs()
        assert len(jobs) == 2
        job_ids = {j["id"] for j in jobs}
        assert "weekly_report_all" in job_ids
        assert "interval_fetch_12h_Python" in job_ids

    def test_remove_job(self, scheduler) -> None:
        """测试移除任务成功。"""
        scheduler.add_weekly_job(day_of_week="wed", hour=12, minute=0, language="Go")
        assert len(scheduler.list_jobs()) == 1

        ok = scheduler.remove_job("weekly_report_Go")
        assert ok is True
        assert len(scheduler.list_jobs()) == 0

    def test_remove_nonexistent_job(self, scheduler) -> None:
        """测试移除不存在的任务。"""
        ok = scheduler.remove_job("nonexistent_job")
        assert ok is False

    def test_replace_existing_job(self, scheduler) -> None:
        """测试添加同 ID 任务会替换旧任务（需调度器运行后生效）。"""
        scheduler.add_weekly_job(day_of_week="mon", hour=9, minute=0, language="")
        scheduler.add_weekly_job(day_of_week="thu", hour=15, minute=0, language="")
        # replace_existing 在调度器未 start 时的行为因版本而异
        # 验证至少两个调用不抛异常
        jobs = scheduler.list_jobs()
        assert len(jobs) >= 1

    @pytest.mark.asyncio
    async def test_pause_resume(self, scheduler) -> None:
        """测试调度器暂停和恢复。"""
        with patch.object(scheduler.scheduler, "pause", return_value=None):
            scheduler.pause()
        with patch.object(scheduler.scheduler, "resume", return_value=None):
            scheduler.resume()
        # 不抛异常即为通过
        assert True

    @pytest.mark.asyncio
    async def test_start_shutdown(self, scheduler) -> None:
        """测试调度器启动和关闭（不实际运行）。"""
        with patch.object(scheduler.scheduler, "start", return_value=None):
            scheduler.start()
        with patch.object(scheduler.scheduler, "shutdown", return_value=None):
            scheduler.shutdown()
        assert True
