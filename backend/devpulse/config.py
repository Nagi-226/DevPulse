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
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10

    # ── GitHub ──────────────────────────────────────────
    GITHUB_TOKEN: str = ""
    GITHUB_API_BASE_URL: str = "https://api.github.com"
    GITHUB_TRENDING_URL: str = "https://github.com/trending"

    # ── 爬虫 ────────────────────────────────────────────
    CRAWLER_TIMEOUT: int = 30
    CRAWLER_MAX_RETRIES: int = 3
    CRAWLER_USER_AGENT: str = "DevPulse/0.0.2"

    # ── LLM ─────────────────────────────────────────────
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-5-haiku-latest"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:7b"
    LLM_PROVIDER: str = "openai"
    LLM_MAX_TOKENS: int = 500
    LLM_TEMPERATURE: float = 0.3

    # ── 运行时 ──────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    CACHE_TTL: int = 3600

    # ── 调度器 ──────────────────────────────────────────
    SCHEDULER_ENABLED: bool = True
    SCHEDULER_CRON_DAY: str = "mon"
    SCHEDULER_CRON_HOUR: int = 9
    SCHEDULER_CRON_MINUTE: int = 0


settings = Settings()
