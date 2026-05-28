"""FastAPI 依赖注入 — JWT 认证中间件."""

from __future__ import annotations

import logging

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

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

    return {"user_id": int(user_id), "email": email or ""}


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
