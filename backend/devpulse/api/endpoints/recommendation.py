"""AI 推荐 API 端点."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, Query, Request

from devpulse.api.dependencies import get_optional_user
from devpulse.core.database import Database
from devpulse.services.recommendation import RecommendationEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/repos", tags=["recommendations"])


@router.get("/recommended")
async def get_recommended(
    request: Request,
    limit: int = Query(10, ge=1, le=50, description="返回条数"),
    current_user: dict | None = Depends(get_optional_user),
) -> dict[str, Any]:
    """获取个性化推荐列表.

    支持三层降级策略:
        - L1: 协同过滤 (用户 ≥ 3 条行为记录)
        - L2: 内容过滤 (行为不足但有语言偏好)
        - L3: 全局热门 (匿名用户 / 零行为)
    """
    db: Database = request.app.state.db
    user_id = current_user["user_id"] if current_user else None

    async with db.get_session() as session:
        result = await RecommendationEngine.get_recommendations(
            session, user_id=user_id, limit=limit
        )
        return {"code": 0, "message": "success", "data": result}
