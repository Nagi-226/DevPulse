"""认证 API 端点 — 注册/登录/Token 刷新/用户信息."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status

from devpulse.api.dependencies import get_current_user
from devpulse.core.database import Database
from devpulse.services.auth_service import auth_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])

# 邮箱正则（基础验证）
_EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


def _validate_password(password: str) -> None:
    """验证密码强度（最小 8 位 + 字母 + 数字）.

    Raises:
        HTTPException 422: 密码不符合要求.
    """
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="密码长度至少 8 位",
        )
    if not re.search(r"[a-zA-Z]", password):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="密码必须包含至少一个字母",
        )
    if not re.search(r"\d", password):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="密码必须包含至少一个数字",
        )


def _validate_email(email: str) -> None:
    """验证邮箱格式.

    Raises:
        HTTPException 422: 邮箱格式无效.
    """
    if not _EMAIL_PATTERN.match(email):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="邮箱格式无效",
        )


@router.post("/register")
async def register(request: Request) -> dict[str, Any]:
    """用户注册.

    POST /auth/register
    Body: {email, password, confirm_password, display_name?}

    Returns:
        {access_token, refresh_token, token_type, expires_in, user}
    """
    from sqlalchemy import select

    from devpulse.core.models import User

    body = await request.json()
    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""
    confirm_password = body.get("confirm_password") or ""
    display_name = (body.get("display_name") or "").strip() or None

    # 校验
    _validate_email(email)
    _validate_password(password)
    if password != confirm_password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="两次输入的密码不一致",
        )

    db: Database = request.app.state.db
    async with db.get_session() as session:
        # 检查邮箱是否已注册
        result = await session.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="该邮箱已被注册",
            )

        # 创建用户
        password_hash = auth_service.hash_password(password)
        user = User(
            email=email,  # type: ignore[arg-type]
            password_hash=password_hash,  # type: ignore[arg-type]
            display_name=display_name,  # type: ignore[arg-type]
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        # 签发 Token
        access_token = auth_service.create_access_token(user.id, user.email)  # type: ignore[arg-type]
        refresh_token = auth_service.create_refresh_token(user.id)  # type: ignore[arg-type]

        logger.info("User registered: %s (id=%d)", email, user.id)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 86400,  # 24 小时
            "user": {
                "id": user.id,
                "email": user.email,
                "display_name": user.display_name,
                "created_at": user.created_at.isoformat() if user.created_at else None,
            },
        }


@router.post("/login")
async def login(request: Request) -> dict[str, Any]:
    """用户登录.

    POST /auth/login
    Body: {email, password}

    Returns:
        {access_token, refresh_token, token_type, expires_in, user}
    """
    from sqlalchemy import select

    from devpulse.core.models import User

    body = await request.json()
    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""

    if not email or not password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="邮箱和密码不能为空",
        )

    db: Database = request.app.state.db
    async with db.get_session() as session:
        result = await session.execute(select(User).where(User.email == email))
        user: User | None = result.scalar_one_or_none()

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="邮箱或密码错误",
            )

        if not auth_service.verify_password(password, user.password_hash):  # type: ignore[arg-type]
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="邮箱或密码错误",
            )

        # 签发 Token
        access_token = auth_service.create_access_token(user.id, user.email)  # type: ignore[arg-type]
        refresh_token = auth_service.create_refresh_token(user.id)  # type: ignore[arg-type]

        logger.info("User logged in: %s (id=%d)", email, user.id)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 86400,
            "user": {
                "id": user.id,
                "email": user.email,
                "display_name": user.display_name,
                "push_enabled": user.push_enabled,
                "push_weekly_report": user.push_weekly_report,
                "push_important_project": user.push_important_project,
                "created_at": user.created_at.isoformat() if user.created_at else None,
            },
        }


@router.get("/me")
async def get_me(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    """获取当前登录用户信息.

    GET /auth/me
    Headers: Authorization: Bearer <access_token>

    Returns:
        用户信息字典.
    """
    from sqlalchemy import select

    from devpulse.core.models import User

    db: Database = request.app.state.db
    async with db.get_session() as session:
        result = await session.execute(
            select(User).where(User.id == current_user["user_id"])
        )
        user: User | None = result.scalar_one_or_none()

        if user is None:
            raise HTTPException(status_code=404, detail="用户不存在")

        return {
            "id": user.id,
            "email": user.email,
            "display_name": user.display_name,
            "push_enabled": user.push_enabled,
            "push_weekly_report": user.push_weekly_report,
            "push_important_project": user.push_important_project,
            "fcm_token": user.fcm_token,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        }


@router.post("/refresh")
async def refresh_token(request: Request) -> dict[str, Any]:
    """刷新 access token.

    POST /auth/refresh
    Body: {refresh_token}

    Returns:
        新的 {access_token, refresh_token, token_type, expires_in}
    """
    body = await request.json()
    refresh_token_str = body.get("refresh_token") or ""

    if not refresh_token_str:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="缺少 refresh_token",
        )

    try:
        payload = auth_service.decode_token(refresh_token_str)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token 已过期，请重新登录",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token 无效",
        )

    if not auth_service.is_refresh_token(payload):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请使用 refresh token",
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 缺少用户标识",
        )

    # 查找用户确认仍存在
    from sqlalchemy import select

    from devpulse.core.models import User

    db: Database = request.app.state.db
    async with db.get_session() as session:
        result = await session.execute(
            select(User).where(User.id == int(user_id))
        )
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=404, detail="用户不存在")

        # 轮换 Token（发布新的 refresh token，旧 token 失效）
        new_access = auth_service.create_access_token(user.id, user.email)  # type: ignore[arg-type]
        new_refresh = auth_service.create_refresh_token(user.id)  # type: ignore[arg-type]

        logger.info("Token refreshed for user %d", user.id)
        return {
            "access_token": new_access,
            "refresh_token": new_refresh,
            "token_type": "bearer",
            "expires_in": 86400,
        }


@router.put("/fcm-token")
async def update_fcm_token(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> dict[str, str]:
    """更新当前用户的 FCM Token.

    PUT /auth/fcm-token
    Body: {fcm_token}

    Returns:
        {message: "FCM token updated"}
    """
    from sqlalchemy import select

    from devpulse.core.models import User

    body = await request.json()
    fcm_token = (body.get("fcm_token") or "").strip()

    db: Database = request.app.state.db
    async with db.get_session() as session:
        result = await session.execute(
            select(User).where(User.id == current_user["user_id"])
        )
        user: User | None = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=404, detail="用户不存在")

        user.fcm_token = fcm_token if fcm_token else None  # type: ignore[assignment]
        await session.commit()

    return {"message": "FCM token updated"}


@router.put("/preferences")
async def update_preferences(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    """更新当前用户的推送偏好.

    PUT /auth/preferences
    Body: {push_enabled?, push_weekly_report?, push_important_project?}

    Returns:
        更新后的偏好设置.
    """
    from sqlalchemy import select

    from devpulse.core.models import User

    body = await request.json()

    db: Database = request.app.state.db
    async with db.get_session() as session:
        result = await session.execute(
            select(User).where(User.id == current_user["user_id"])
        )
        user: User | None = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=404, detail="用户不存在")

        if "push_enabled" in body:
            user.push_enabled = bool(body["push_enabled"])  # type: ignore[assignment]
        if "push_weekly_report" in body:
            user.push_weekly_report = bool(body["push_weekly_report"])  # type: ignore[assignment]
        if "push_important_project" in body:
            user.push_important_project = bool(body["push_important_project"])  # type: ignore[assignment]

        await session.commit()
        await session.refresh(user)

    return {
        "push_enabled": user.push_enabled,
        "push_weekly_report": user.push_weekly_report,
        "push_important_project": user.push_important_project,
    }
