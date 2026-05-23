"""调度器管理 API 端点。

提供定时任务的增删查、暂停与恢复功能。
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter(prefix="/scheduler", tags=["scheduler"])


class JobCreateRequest(BaseModel):
    """创建定时任务的请求体。"""

    type: str  # "weekly" 或 "interval"
    language: str = ""
    since: str = "weekly"
    day_of_week: str | None = None
    hour: int | None = None
    minute: int | None = None
    interval_hours: int | None = None


@router.get("/jobs")
async def list_jobs(request: Request) -> list[dict[str, Any]]:
    """列出所有已注册的定时任务。

    Returns:
        任务信息列表。
    """
    scheduler = getattr(request.app.state, "scheduler", None)
    if scheduler is None:
        return []
    return scheduler.list_jobs()


@router.post("/jobs")
async def add_job(request: Request, body: JobCreateRequest) -> dict[str, str]:
    """添加新的定时任务。

    Args:
        body: 任务配置。

    Returns:
        操作结果。

    Raises:
        HTTPException: 调度器未启用或任务类型无效。
    """
    scheduler = getattr(request.app.state, "scheduler", None)
    if scheduler is None:
        raise HTTPException(status_code=503, detail="调度器未启用")

    if body.type == "weekly":
        scheduler.add_weekly_job(
            day_of_week=body.day_of_week or "mon",
            hour=body.hour or 9,
            minute=body.minute or 0,
            language=body.language,
        )
        return {"status": "ok", "message": "周任务已添加"}
    elif body.type == "interval":
        scheduler.add_interval_job(
            hours=body.interval_hours or 6,
            language=body.language,
            since=body.since,
        )
        return {"status": "ok", "message": "间隔任务已添加"}
    else:
        raise HTTPException(status_code=400, detail=f"不支持的任务类型: {body.type}")


@router.delete("/jobs/{job_id}")
async def delete_job(request: Request, job_id: str) -> dict[str, str]:
    """移除指定定时任务。

    Args:
        job_id: 任务 ID。

    Returns:
        操作结果。

    Raises:
        HTTPException: 调度器未启用或任务不存在。
    """
    scheduler = getattr(request.app.state, "scheduler", None)
    if scheduler is None:
        raise HTTPException(status_code=503, detail="调度器未启用")

    ok = scheduler.remove_job(job_id)
    if not ok:
        raise HTTPException(status_code=404, detail=f"任务 '{job_id}' 不存在")
    return {"status": "ok", "message": f"任务 '{job_id}' 已移除"}


@router.post("/pause")
async def pause_scheduler(request: Request) -> dict[str, str]:
    """暂停调度器所有任务。

    Returns:
        操作结果。

    Raises:
        HTTPException: 调度器未启用。
    """
    scheduler = getattr(request.app.state, "scheduler", None)
    if scheduler is None:
        raise HTTPException(status_code=503, detail="调度器未启用")
    scheduler.pause()
    return {"status": "ok", "message": "调度器已暂停"}


@router.post("/resume")
async def resume_scheduler(request: Request) -> dict[str, str]:
    """恢复调度器所有任务。

    Returns:
        操作结果。

    Raises:
        HTTPException: 调度器未启用。
    """
    scheduler = getattr(request.app.state, "scheduler", None)
    if scheduler is None:
        raise HTTPException(status_code=503, detail="调度器未启用")
    scheduler.resume()
    return {"status": "ok", "message": "调度器已恢复"}
