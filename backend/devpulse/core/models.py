"""SQLAlchemy ORM 数据模型 — User + Repository + WeeklyReport + Favorite + StarHistory."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    """用户表 — JWT 认证 + 推送偏好."""

    __tablename__ = "users"

    id: int = Column(Integer, primary_key=True, autoincrement=True)  # type: ignore[assignment]
    email: str = Column(String(255), unique=True, nullable=False, index=True)  # type: ignore[assignment]
    password_hash: str = Column(String(255), nullable=False)  # type: ignore[assignment]
    display_name: str | None = Column(String(100))  # type: ignore[assignment]
    push_enabled: bool = Column(Boolean, default=True)  # type: ignore[assignment]
    push_weekly_report: bool = Column(Boolean, default=True)  # type: ignore[assignment]
    push_important_project: bool = Column(Boolean, default=False)  # type: ignore[assignment]
    fcm_token: str | None = Column(String(500))  # type: ignore[assignment]
    created_at: datetime = Column(DateTime, default=lambda: datetime.now(timezone.utc))  # type: ignore[assignment]
    updated_at: datetime = Column(  # type: ignore[assignment]
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}')>"


class Repository(Base):
    """GitHub 仓库元数据表."""

    __tablename__ = "repositories"

    id: int = Column(Integer, primary_key=True, autoincrement=True)  # type: ignore[assignment]
    full_name: str = Column(String(200), unique=True, nullable=False, index=True)  # type: ignore[assignment]
    owner: str = Column(String(100), nullable=False, index=True)  # type: ignore[assignment]
    name: str = Column(String(100), nullable=False)  # type: ignore[assignment]
    description: str | None = Column(Text)  # type: ignore[assignment]
    language: str | None = Column(String(50))  # type: ignore[assignment]
    topics: list[str] | None = Column(JSON)  # type: ignore[assignment]
    total_stars: int = Column(Integer, default=0)  # type: ignore[assignment]
    stars_since: int = Column(Integer, default=0)  # type: ignore[assignment]
    forks: int = Column(Integer, default=0)  # type: ignore[assignment]
    forks_since: int = Column(Integer, default=0)  # type: ignore[assignment]
    open_issues: int = Column(Integer, default=0)  # type: ignore[assignment]
    created_at: datetime | None = Column(DateTime)  # type: ignore[assignment]
    updated_at: datetime | None = Column(DateTime)  # type: ignore[assignment]
    url: str | None = Column(String(500))  # type: ignore[assignment]
    has_readme: bool = Column(Boolean, default=False)  # type: ignore[assignment]
    readme_content: str | None = Column(Text)  # type: ignore[assignment]
    readme_summary: str | None = Column(Text)  # type: ignore[assignment]
    key_points: list[str] | None = Column(JSON)  # type: ignore[assignment]
    tags: list[str] | None = Column(JSON)  # type: ignore[assignment]
    crawled_at: datetime | None = Column(DateTime)  # type: ignore[assignment]
    summarized_at: datetime | None = Column(DateTime)  # type: ignore[assignment]
    trending_rank: int | None = Column(Integer)  # type: ignore[assignment]
    trending_since: str | None = Column(String(20))  # type: ignore[assignment]
    source: str = Column(String(20), default="github")  # type: ignore[assignment]

    __table_args__ = (
        Index("idx_repo_language", "language"),
        Index("idx_repo_stars", "total_stars"),
        Index("idx_repo_trending", "trending_rank", "trending_since"),
    )

    def __repr__(self) -> str:
        return f"<Repository(id={self.id}, full_name='{self.full_name}')>"


class WeeklyReport(Base):
    """周报聚合表."""

    __tablename__ = "weekly_reports"

    id: int = Column(Integer, primary_key=True, autoincrement=True)  # type: ignore[assignment]
    week_start: datetime = Column(DateTime, unique=True, nullable=False, index=True)  # type: ignore[assignment]
    week_end: datetime = Column(DateTime, nullable=False)  # type: ignore[assignment]
    language_filter: str | None = Column(String(50))  # type: ignore[assignment]
    source_filter: str = Column(String(20), default="github")  # type: ignore[assignment]
    total_repos: int = Column(Integer, default=0)  # type: ignore[assignment]
    top_repos: list[int] | None = Column(JSON)  # type: ignore[assignment]
    overview_text: str | None = Column(Text)  # type: ignore[assignment]
    generated_at: datetime | None = Column(DateTime)  # type: ignore[assignment]
    published: bool = Column(Boolean, default=False)  # type: ignore[assignment]
    published_at: datetime | None = Column(DateTime)  # type: ignore[assignment]

    def __repr__(self) -> str:
        return f"<WeeklyReport(id={self.id}, week_start='{self.week_start}')>"


class Favorite(Base):
    """用户收藏关联表 — 关联 User 和 Repository."""

    __tablename__ = "favorites"

    id: int = Column(Integer, primary_key=True, autoincrement=True)  # type: ignore[assignment]
    user_id: int = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)  # type: ignore[assignment]
    repo_id: int = Column(Integer, ForeignKey("repositories.id"), nullable=False, index=True)  # type: ignore[assignment]
    created_at: datetime = Column(DateTime, default=lambda: datetime.now(timezone.utc))  # type: ignore[assignment]

    # 关系
    user = relationship("User", backref="favorites")
    repo = relationship("Repository", backref="favorited_by")

    __table_args__ = (
        Index("idx_fav_user_repo", "user_id", "repo_id", unique=True),
    )

    def __repr__(self) -> str:
        return f"<Favorite(id={self.id}, user_id={self.user_id}, repo_id={self.repo_id})>"


class StarHistory(Base):
    """Star 历史快照表."""

    __tablename__ = "star_history"

    id: int = Column(Integer, primary_key=True, autoincrement=True)  # type: ignore[assignment]
    repo_id: int = Column(Integer, nullable=False, index=True)  # type: ignore[assignment]
    total_stars: int = Column(Integer, nullable=False)  # type: ignore[assignment]
    recorded_at: datetime = Column(DateTime, nullable=False, index=True)  # type: ignore[assignment]

    __table_args__ = (
        Index("idx_sh_repo_date", "repo_id", "recorded_at"),
    )

    def __repr__(self) -> str:
        return f"<StarHistory(id={self.id}, repo_id={self.repo_id}, stars={self.total_stars})>"
