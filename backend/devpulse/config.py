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

    # ── GitLab ──────────────────────────────────────────
    GITLAB_TOKEN: str = ""
    GITLAB_API_BASE_URL: str = "https://gitlab.com/api/v4"
    GITLAB_EXPLORE_URL: str = "https://gitlab.com/explore"

    # ── Gitee ───────────────────────────────────────────
    GITEE_TOKEN: str = ""
    GITEE_API_BASE_URL: str = "https://gitee.com/api/v5"
    GITEE_EXPLORE_URL: str = "https://gitee.com/explore"

    # ── 爬虫 ────────────────────────────────────────────
    CRAWLER_TIMEOUT: int = 30
    CRAWLER_MAX_RETRIES: int = 3
    CRAWLER_USER_AGENT: str = "DevPulse/0.3.0"

    # ── LLM ─────────────────────────────────────────────
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-5-haiku-latest"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:7b"
    # ── DeepSeek ────────────────────────────────────────
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_MODEL: str = "deepseek-chat"
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    LLM_PROVIDER: str = "deepseek"
    LLM_MAX_TOKENS: int = 500
    LLM_TEMPERATURE: float = 0.3
    # ── LLM 摘要成本控制 ────────────────────────────────
    LLM_SUMMARY_BATCH_SIZE: int = 5

    # ── JWT 认证 ────────────────────────────────────────
    JWT_SECRET_KEY: str = "devpulse-dev-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 24
    JWT_REFRESH_EXPIRE_DAYS: int = 7

    # ── Firebase Cloud Messaging ────────────────────────
    FCM_CREDENTIALS_PATH: str = ""
    FCM_ENABLED: bool = False

    # ── 运行时 ──────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    CACHE_TTL: int = 3600
    CACHE_TTL_DAYS: int = 7
    RENDER: bool = False  # 是否运行在 Render.com 平台
    API_BASE_URL: str = ""  # 部署后公开访问的 API 地址

    # ── 调度器 ──────────────────────────────────────────
    SCHEDULER_ENABLED: bool = True
    SCHEDULER_CRON_DAY: str = "mon"
    SCHEDULER_CRON_HOUR: int = 9
    SCHEDULER_CRON_MINUTE: int = 0

    # ── Star History ────────────────────────────────────
    STAR_HISTORY_RETENTION_DAYS: int = 90

    # ── MetaGPT ─────────────────────────────────────────
    META_GPT_ENABLED: bool = False

    # ── CORS ────────────────────────────────────────────
    CORS_ORIGINS: list[str] = [
        "http://localhost:1420",
        "http://localhost:5173",
        "http://127.0.0.1:1420",
        "tauri://localhost",
        "https://tauri.localhost",
        "http://tauri.localhost",
        "capacitor://localhost",
        "https://devpulse.app",
    ]

    # ── 支持的语言列表 ──────────────────────────────────
    SUPPORTED_LANGUAGES: list[str] = [
        "all", "Python", "JavaScript", "TypeScript", "Go", "Rust",
        "Java", "C++", "C", "C#", "Ruby", "PHP", "Swift", "Kotlin",
        "Dart", "R", "Julia", "Scala", "Haskell", "Elixir", "Clojure",
        "Lua", "Shell", "Objective-C", "Vue", "CSS", "HTML",
        "Jupyter Notebook", "Zig", "Erlang", "Perl", "MATLAB",
    ]


settings = Settings()
