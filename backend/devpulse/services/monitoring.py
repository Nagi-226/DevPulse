"""Sentry 错误追踪服务 — FastAPI 集成."""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

_sentry_initialized: bool = False


def init_sentry(
    dsn: str,
    environment: str = "production",
    traces_sample_rate: float = 0.2,
    profiles_sample_rate: float = 0.1,
) -> None:
    """初始化 Sentry SDK（FastAPI integration）.

    只在首次调用时初始化，重复调用无副作用.

    Args:
        dsn: Sentry DSN URL.
        environment: 环境标识 (production/staging/development).
        traces_sample_rate: 性能追踪采样率 (0.0-1.0).
        profiles_sample_rate: 性能分析采样率 (0.0-1.0).
    """
    global _sentry_initialized

    if _sentry_initialized:
        logger.debug("Sentry already initialized, skipping.")
        return

    if not dsn:
        logger.warning("SENTRY_DSN not set, error tracking disabled.")
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration

        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            traces_sample_rate=traces_sample_rate,
            profiles_sample_rate=profiles_sample_rate,
            integrations=[
                StarletteIntegration(
                    transaction_style="endpoint",
                ),
                FastApiIntegration(
                    transaction_style="endpoint",
                ),
            ],
            send_default_pii=False,
            max_breadcrumbs=100,
            attach_stacktrace=True,
        )
        _sentry_initialized = True
        logger.info(
            "Sentry initialized: env=%s, traces_rate=%.2f",
            environment,
            traces_sample_rate,
        )
    except ImportError:
        logger.warning("sentry_sdk not installed, error tracking disabled.")
    except Exception:
        logger.exception("Failed to initialize Sentry")


def set_sentry_context(user_id: int | None = None, email: str | None = None) -> None:
    """设置 Sentry 用户上下文（用于错误关联）.

    Args:
        user_id: 当前用户 ID.
        email: 当前用户邮箱.
    """
    if not _sentry_initialized:
        return
    try:
        import sentry_sdk

        if user_id is not None:
            sentry_sdk.set_user({"id": str(user_id), "email": email or ""})
    except Exception:
        pass


def capture_exception(exc: Exception, extra: dict | None = None) -> None:
    """手动上报异常到 Sentry.

    Args:
        exc: 异常实例.
        extra: 附加上下文信息.
    """
    if not _sentry_initialized:
        return
    try:
        import sentry_sdk

        with sentry_sdk.push_scope() as scope:
            if extra:
                for key, value in extra.items():
                    scope.set_extra(key, value)
            sentry_sdk.capture_exception(exc)
    except Exception:
        pass
