"""JWT 认证服务 — Token 签发/验证 + bcrypt 密码哈希."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from devpulse.config import settings

logger = logging.getLogger(__name__)

# bcrypt 密码哈希上下文（cost factor = 12）
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """JWT 认证服务.

    提供密码哈希、JWT Token 签发与验证功能。

    Token 策略:
        - access_token: 24 小时有效期，用于 API 请求认证
        - refresh_token: 7 天有效期，用于无感刷新 access_token
    """

    def __init__(
        self,
        secret_key: str | None = None,
        algorithm: str | None = None,
        access_expire_hours: int | None = None,
        refresh_expire_days: int | None = None,
    ) -> None:
        self._secret_key = secret_key or settings.JWT_SECRET_KEY
        self._algorithm = algorithm or settings.JWT_ALGORITHM
        self._access_expire = access_expire_hours or settings.JWT_EXPIRE_HOURS
        self._refresh_expire = refresh_expire_days or settings.JWT_REFRESH_EXPIRE_DAYS

    # ── 密码哈希 ──────────────────────────────────────

    @staticmethod
    def hash_password(password: str) -> str:
        """对明文密码进行 bcrypt 哈希.

        Args:
            password: 明文密码.

        Returns:
            bcrypt 哈希字符串.
        """
        return _pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """验证明文密码是否匹配 bcrypt 哈希.

        Args:
            plain_password: 明文密码.
            hashed_password: bcrypt 哈希字符串.

        Returns:
            是否匹配.
        """
        return _pwd_context.verify(plain_password, hashed_password)

    # ── JWT Token ─────────────────────────────────────

    def create_access_token(self, user_id: int, email: str) -> str:
        """签发 access token（24h 有效期）.

        Args:
            user_id: 用户 ID.
            email: 用户邮箱.

        Returns:
            JWT access token 字符串.
        """
        now = datetime.now(timezone.utc)
        payload = {
            "sub": user_id,
            "email": email,
            "iat": now,
            "exp": now + timedelta(hours=self._access_expire),
            "type": "access",
        }
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    def create_refresh_token(self, user_id: int) -> str:
        """签发 refresh token（7d 有效期）.

        Args:
            user_id: 用户 ID.

        Returns:
            JWT refresh token 字符串.
        """
        now = datetime.now(timezone.utc)
        payload = {
            "sub": user_id,
            "iat": now,
            "exp": now + timedelta(days=self._refresh_expire),
            "type": "refresh",
        }
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    def decode_token(self, token: str) -> dict:
        """解码并验证 JWT Token.

        Args:
            token: JWT 字符串.

        Returns:
            解码后的 payload 字典（含 sub/email/exp/iat/type）.

        Raises:
            jwt.ExpiredSignatureError: Token 已过期.
            jwt.InvalidTokenError: Token 无效.
        """
        return jwt.decode(token, self._secret_key, algorithms=[self._algorithm])  # type: ignore[return-value]

    def is_access_token(self, payload: dict) -> bool:
        """判断 payload 是否为 access token."""
        return payload.get("type") == "access"

    def is_refresh_token(self, payload: dict) -> bool:
        """判断 payload 是否为 refresh token."""
        return payload.get("type") == "refresh"


# 全局单例
auth_service = AuthService()
