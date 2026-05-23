"""测试：调度器 API 端点。"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from devpulse.main import app
from devpulse.services.scheduler import DevPulseScheduler


class TestSchedulerAPI:
    """调度器端点集成测试。"""

    @pytest.fixture
    def mock_scheduler(self) -> MagicMock:
        """创建 mock 调度器。"""
        scheduler = MagicMock(spec=DevPulseScheduler)
        scheduler.list_jobs.return_value = [
            {
                "id": "weekly_report_all",
                "name": "周报生成 (全语言) — 每mon 09:00",
                "next_run": "2026-05-25 09:00:00+08:00",
                "trigger": "cron[day_of_week='mon', hour='9', minute='0']",
            }
        ]
        scheduler.add_weekly_job.return_value = None
        scheduler.add_interval_job.return_value = None
        scheduler.remove_job.return_value = True
        scheduler.pause.return_value = None
        scheduler.resume.return_value = None
        return scheduler

    @pytest.fixture
    async def client(self, mock_scheduler) -> AsyncClient:
        """创建测试客户端，注入 mock 调度器。"""
        app.state.scheduler = mock_scheduler

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    @pytest.mark.asyncio
    async def test_list_jobs_endpoint(self, client, mock_scheduler) -> None:
        """GET /scheduler/jobs 返回任务列表。"""
        response = await client.get("/scheduler/jobs")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "weekly_report_all"

    @pytest.mark.asyncio
    async def test_add_weekly_job_endpoint(self, client, mock_scheduler) -> None:
        """POST /scheduler/jobs 添加周任务。"""
        response = await client.post(
            "/scheduler/jobs",
            json={
                "type": "weekly",
                "language": "Python",
                "day_of_week": "fri",
                "hour": 18,
                "minute": 30,
            },
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        mock_scheduler.add_weekly_job.assert_called_once_with(
            day_of_week="fri",
            hour=18,
            minute=30,
            language="Python",
        )

    @pytest.mark.asyncio
    async def test_add_interval_job_endpoint(self, client, mock_scheduler) -> None:
        """POST /scheduler/jobs 添加间隔任务。"""
        response = await client.post(
            "/scheduler/jobs",
            json={
                "type": "interval",
                "language": "",
                "since": "daily",
                "interval_hours": 6,
            },
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        mock_scheduler.add_interval_job.assert_called_once_with(
            hours=6,
            language="",
            since="daily",
        )

    @pytest.mark.asyncio
    async def test_add_job_invalid_type(self, client, mock_scheduler) -> None:
        """POST /scheduler/jobs 无效任务类型返回 400。"""
        response = await client.post(
            "/scheduler/jobs",
            json={"type": "unknown"},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_delete_job_endpoint(self, client, mock_scheduler) -> None:
        """DELETE /scheduler/jobs/{id} 移除任务。"""
        mock_scheduler.remove_job.return_value = True
        response = await client.delete("/scheduler/jobs/weekly_report_all")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        mock_scheduler.remove_job.assert_called_once_with("weekly_report_all")

    @pytest.mark.asyncio
    async def test_delete_nonexistent_job(self, client, mock_scheduler) -> None:
        """DELETE /scheduler/jobs/{id} 不存在的任务返回 404。"""
        mock_scheduler.remove_job.return_value = False
        response = await client.delete("/scheduler/jobs/nonexistent")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_pause_endpoint(self, client, mock_scheduler) -> None:
        """POST /scheduler/pause 暂停调度器。"""
        response = await client.post("/scheduler/pause")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        mock_scheduler.pause.assert_called_once()

    @pytest.mark.asyncio
    async def test_resume_endpoint(self, client, mock_scheduler) -> None:
        """POST /scheduler/resume 恢复调度器。"""
        response = await client.post("/scheduler/resume")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        mock_scheduler.resume.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_scheduler_returns_empty_list(self) -> None:
        """调度器未启用时端点返回空列表。"""
        original = getattr(app.state, "scheduler", None)
        try:
            app.state.scheduler = None
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.get("/scheduler/jobs")
                assert response.status_code == 200
                assert response.json() == []
        finally:
            app.state.scheduler = original
