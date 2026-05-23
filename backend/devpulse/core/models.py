"""SQLAlchemy ORM 数据模型 — Repository + WeeklyReport."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, Index, Integer, String, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


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
    total_repos: int = Column(Integer, default=0)  # type: ignore[assignment]
    top_repos: list[int] | None = Column(JSON)  # type: ignore[assignment]
    overview_text: str | None = Column(Text)  # type: ignore[assignment]
    generated_at: datetime | None = Column(DateTime)  # type: ignore[assignment]
    published: bool = Column(Boolean, default=False)  # type: ignore[assignment]
    published_at: datetime | None = Column(DateTime)  # type: ignore[assignment]

    def __repr__(self) -> str:
        return f"<WeeklyReport(id={self.id}, week_start='{self.week_start}')>"
