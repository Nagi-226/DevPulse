"""DevPulse 配置管理 — 基于 Pydantic Settings."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """DevPulse 应用配置，自动从 .env 文件加载."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── 数据库 ──────────────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./devpulse.db"

    # ── GitHub ──────────────────────────────────────────
    GITHUB_TOKEN: str = ""

    # ── LLM ─────────────────────────────────────────────
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    LLM_PROVIDER: str = "openai"

    # ── 运行时 ──────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    CACHE_TTL: int = 3600


settings = Settings()
