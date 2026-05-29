"""FastAPI 依赖注入 — JWT 认证中间件 + Admin 鉴权."""

from __future__ import annotations

import logging

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select

from devpulse.core.models import User
from devpulse.services.auth_service import auth_service

logger = logging.getLogger(__name__)

# Bearer Token 安全方案
security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    """从 Bearer Token 解析当前用户信息.

    用作 FastAPI 依赖注入，在需要认证的端点参数中声明即可:
        user: dict = Depends(get_current_user)

    Args:
        request: FastAPI Request 对象.
        credentials: HTTP Bearer Token 凭证.

    Returns:
        包含 user_id 和 email 的字典.

    Raises:
        HTTPException 401: Token 缺失、无效或过期.
        HTTPException 403: 用户已被封禁.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证 Token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        payload = auth_service.decode_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 已过期，请重新登录",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 无效",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not auth_service.is_access_token(payload):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请使用 access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    email = payload.get("email")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 缺少用户标识",
        )

    user_id_int = int(user_id)

    # 检查用户是否被封禁
    try:
        from devpulse.core.database import Database

        db: Database | None = getattr(request.app.state, "db", None)
        if db is not None:
            async with db.get_session() as session:
                result = await session.execute(
                    select(User).where(User.id == user_id_int)
                )
                user_row = result.scalar_one_or_none()
                if user_row is not None and not user_row.is_active:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="账户已被封禁",
                    )
    except HTTPException:
        raise
    except Exception:
        pass  # 数据库不可用时跳过检查

    return {"user_id": user_id_int, "email": email or ""}


async def get_optional_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict | None:
    """可选认证：有 Token 则解析，无则返回 None.

    用于同时支持匿名和已登录用户的端点.
    """
    if credentials is None:
        return None

    try:
        payload = auth_service.decode_token(credentials.credentials)
        if auth_service.is_access_token(payload):
            user_id = payload.get("sub")
            email = payload.get("email")
            if user_id is not None:
                return {"user_id": int(user_id), "email": email or ""}
    except Exception:
        pass

    return None


async def get_admin_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    """Admin 角色鉴权依赖.

    用法:
        admin_user: dict = Depends(get_admin_user)

    先验证 JWT Token 有效性，再检查 user.role == "admin".

    Raises:
        HTTPException 401: Token 缺失或无效.
        HTTPException 403: 非 admin 角色.
    """
    # 基础 JWT 认证
    current_user = await get_current_user(request, credentials)

    # 检查 admin 角色
    try:
        from devpulse.core.database import Database

        db: Database | None = getattr(request.app.state, "db", None)
        if db is not None:
            async with db.get_session() as session:
                result = await session.execute(
                    select(User).where(User.id == current_user["user_id"])
                )
                user_row = result.scalar_one_or_none()
                if user_row is None:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="用户不存在",
                    )
                if getattr(user_row, "role", "user") != "admin":
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="需要管理员权限",
                    )
                current_user["role"] = user_row.role
                return current_user
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="需要管理员权限",
            )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )
