"""Firebase Cloud Messaging 推送服务."""

from __future__ import annotations

import logging
from typing import Any

from devpulse.config import settings

logger = logging.getLogger(__name__)


class FCMService:
    """FCM 推送服务封装.

    负责 Firebase Admin SDK 初始化、Token 注册、广播推送和单用户推送。
    生产环境需要设置 FCM_CREDENTIALS_PATH 环境变量。
    """

    def __init__(self) -> None:
        self._app: Any = None
        self._initialized = False
        self._init_firebase()

    def _init_firebase(self) -> None:
        """初始化 Firebase Admin SDK."""
        if not settings.FCM_ENABLED and not settings.FCM_CREDENTIALS_PATH:
            logger.info("FCM not configured (FCM_CREDENTIALS_PATH not set), push disabled")
            return

        try:
            import firebase_admin
            from firebase_admin import credentials

            if settings.FCM_CREDENTIALS_PATH:
                cred = credentials.Certificate(settings.FCM_CREDENTIALS_PATH)
            else:
                # 使用应用默认凭证（Google Cloud 环境）
                cred = credentials.ApplicationDefault()

            self._app = firebase_admin.initialize_app(cred)
            self._initialized = True
            logger.info("Firebase Admin SDK initialized")
        except Exception:
            logger.exception("Failed to initialize Firebase Admin SDK")
            self._initialized = False

    @property
    def is_available(self) -> bool:
        """FCM 服务是否可用."""
        return self._initialized

    async def send_to_user(self, user_id: int, title: str, body: str) -> bool:
        """向指定用户发送推送通知.

        Args:
            user_id: 目标用户 ID.
            title: 通知标题.
            body: 通知正文.

        Returns:
            是否发送成功.
        """
        if not self._initialized:
            logger.warning("FCM not initialized, cannot send push to user %d", user_id)
            return False

        # 从数据库读取用户的 FCM Token
        from devpulse.core.database import Database
        from sqlalchemy import select
        from devpulse.core.models import User

        db = Database(
            url=settings.DATABASE_URL,
            echo=settings.DATABASE_ECHO,
        )
        try:
            async with db.get_session() as session:
                result = await session.execute(
                    select(User).where(User.id == user_id)
                )
                user = result.scalar_one_or_none()
                if not user or not user.fcm_token:
                    return False

                return await self._send_single(user.fcm_token, title, body)
        except Exception:
            logger.exception("Failed to send push to user %d", user_id)
            return False
        finally:
            await db.close()

    async def send_weekly_report_notification(self, report_id: int) -> int:
        """向所有启用周报推送的用户发送通知.

        Args:
            report_id: 周报 ID.

        Returns:
            成功发送的用户数.
        """
        if not self._initialized:
            logger.warning("FCM not initialized, cannot send weekly report push")
            return 0

        from devpulse.core.database import Database
        from sqlalchemy import select
        from devpulse.core.models import User

        db = Database(
            url=settings.DATABASE_URL,
            echo=settings.DATABASE_ECHO,
        )
        sent_count = 0
        try:
            async with db.get_session() as session:
                result = await session.execute(
                    select(User).where(
                        User.push_enabled == True,  # noqa: E712
                        User.push_weekly_report == True,  # noqa: E712
                        User.fcm_token.isnot(None),
                    )
                )
                users = result.scalars().all()

                title = "📊 新周报已生成"
                body = f"DevPulse 最新一期 Trending 周报已发布，点击查看本周热门 AI 项目！"

                from firebase_admin import messaging

                tokens = [u.fcm_token for u in users if u.fcm_token]
                if not tokens:
                    return 0

                # 批量发送（multicast 最多 500 个 token）
                for i in range(0, len(tokens), 500):
                    batch = tokens[i : i + 500]
                    message = messaging.MulticastMessage(
                        tokens=batch,
                        notification=messaging.Notification(title=title, body=body),
                        data={"report_id": str(report_id), "type": "weekly_report"},
                    )
                    response = messaging.send_each_for_multicast(message)
                    sent_count += response.success_count

                logger.info(
                    "FCM weekly report push: sent to %d/%d users (report_id=%d)",
                    sent_count, len(users), report_id,
                )
        except Exception:
            logger.exception("Failed to send weekly report FCM push")
        finally:
            await db.close()

        return sent_count

    async def _send_single(self, token: str, title: str, body: str) -> bool:
        """向单个 token 发送推送."""
        try:
            from firebase_admin import messaging

            message = messaging.Message(
                token=token,
                notification=messaging.Notification(title=title, body=body),
            )
            messaging.send(message)
            return True
        except Exception:
            logger.exception("FCM send failed for token")
            return False

    async def register_token(self, user_id: int, fcm_token: str) -> None:
        """注册用户 FCM Token（由 /auth/fcm-token 端点调用）."""
        from devpulse.core.database import Database
        from sqlalchemy import select
        from devpulse.core.models import User

        db = Database(
            url=settings.DATABASE_URL,
            echo=settings.DATABASE_ECHO,
        )
        try:
            async with db.get_session() as session:
                result = await session.execute(
                    select(User).where(User.id == user_id)
                )
                user = result.scalar_one_or_none()
                if user and user.fcm_token != fcm_token:
                    user.fcm_token = fcm_token  # type: ignore[assignment]
                    await session.commit()
        except Exception:
            logger.exception("Failed to register FCM token for user %d", user_id)
        finally:
            await db.close()


# 全局单例
fcm_service = FCMService()
