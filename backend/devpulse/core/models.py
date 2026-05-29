"""SQLAlchemy ORM 数据模型 — User + Repository + WeeklyReport + Favorite + StarHistory + Comment + Like + UserBehavior + DailyStats."""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    """用户表 — JWT 认证 + 推送偏好 + 角色管理."""

    __tablename__ = "users"

    id: int = Column(Integer, primary_key=True, autoincrement=True)  # type: ignore[assignment]
    email: str = Column(String(255), unique=True, nullable=False, index=True)  # type: ignore[assignment]
    password_hash: str = Column(String(255), nullable=False)  # type: ignore[assignment]
    display_name: str | None = Column(String(100))  # type: ignore[assignment]
    role: str = Column(String(20), default="user")  # type: ignore[assignment]  # "user" | "admin"
    is_active: bool = Column(Boolean, default=True)  # type: ignore[assignment]
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

    # 关系
    comments = relationship("Comment", back_populates="user", lazy="dynamic")
    likes = relationship("Like", back_populates="user", lazy="dynamic")
    behaviors = relationship("UserBehavior", back_populates="user", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"


class Repository(Base):
    """GitHub 仓库元数据表（含内容品控字段）."""

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
    # ── Phase 4: 内容品控 ───────────────────────────────
    confidence_score: float | None = Column(Float)  # type: ignore[assignment]  # 0.0-1.0 LLM 置信度
    review_status: str = Column(String(20), default="pending")  # type: ignore[assignment]  # pending|approved|rejected
    review_required: bool = Column(Boolean, default=False)  # type: ignore[assignment]  # 是否需要人工审核

    __table_args__ = (
        Index("idx_repo_language", "language"),
        Index("idx_repo_stars", "total_stars"),
        Index("idx_repo_trending", "trending_rank", "trending_since"),
        Index("idx_repo_review", "review_status"),
    )

    # 关系
    comments = relationship("Comment", back_populates="repo", lazy="dynamic")
    likes = relationship("Like", back_populates="repo", lazy="dynamic")
    behaviors = relationship("UserBehavior", back_populates="repo", lazy="dynamic")
    favorited_by = relationship("Favorite", back_populates="repo", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<Repository(id={self.id}, full_name='{self.full_name}', review='{self.review_status}')>"


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
    repo = relationship("Repository", back_populates="favorited_by")

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


# ═══════════════════════════════════════════════════════════
# Phase 4 新增模型: Comment + Like + UserBehavior + DailyStats
# ═══════════════════════════════════════════════════════════

class Comment(Base):
    """用户评论表."""

    __tablename__ = "comments"

    id: int = Column(Integer, primary_key=True, autoincrement=True)  # type: ignore[assignment]
    user_id: int = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)  # type: ignore[assignment]
    repo_id: int = Column(Integer, ForeignKey("repositories.id"), nullable=False, index=True)  # type: ignore[assignment]
    content: str = Column(Text, nullable=False)  # type: ignore[assignment]
    parent_id: int | None = Column(Integer, ForeignKey("comments.id"), nullable=True)  # type: ignore[assignment]
    is_deleted: bool = Column(Boolean, default=False)  # type: ignore[assignment]
    created_at: datetime = Column(DateTime, default=lambda: datetime.now(timezone.utc))  # type: ignore[assignment]
    updated_at: datetime = Column(  # type: ignore[assignment]
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # 关系
    user = relationship("User", back_populates="comments")
    repo = relationship("Repository", back_populates="comments")
    parent = relationship("Comment", remote_side=[id], backref="replies")

    __table_args__ = (
        Index("idx_comment_repo", "repo_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Comment(id={self.id}, user_id={self.user_id}, repo_id={self.repo_id})>"


class Like(Base):
    """用户点赞表 — user_id + repo_id 唯一."""

    __tablename__ = "likes"

    id: int = Column(Integer, primary_key=True, autoincrement=True)  # type: ignore[assignment]
    user_id: int = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)  # type: ignore[assignment]
    repo_id: int = Column(Integer, ForeignKey("repositories.id"), nullable=False, index=True)  # type: ignore[assignment]
    created_at: datetime = Column(DateTime, default=lambda: datetime.now(timezone.utc))  # type: ignore[assignment]

    # 关系
    user = relationship("User", back_populates="likes")
    repo = relationship("Repository", back_populates="likes")

    __table_args__ = (
        UniqueConstraint("user_id", "repo_id", name="uq_like_user_repo"),
        Index("idx_like_repo", "repo_id"),
    )

    def __repr__(self) -> str:
        return f"<Like(id={self.id}, user_id={self.user_id}, repo_id={self.repo_id})>"


class UserBehavior(Base):
    """用户行为记录表 — 用于推荐引擎训练."""

    __tablename__ = "user_behaviors"

    id: int = Column(Integer, primary_key=True, autoincrement=True)  # type: ignore[assignment]
    user_id: int = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)  # type: ignore[assignment]
    repo_id: int = Column(Integer, ForeignKey("repositories.id"), nullable=False, index=True)  # type: ignore[assignment]
    action_type: str = Column(String(20), nullable=False)  # type: ignore[assignment]  # view|star|like|share|comment
    weight: float = Column(Float, default=1.0)  # type: ignore[assignment]
    created_at: datetime = Column(DateTime, default=lambda: datetime.now(timezone.utc))  # type: ignore[assignment]

    # 关系
    user = relationship("User", back_populates="behaviors")
    repo = relationship("Repository", back_populates="behaviors")

    __table_args__ = (
        Index("idx_ub_user", "user_id", "created_at"),
        Index("idx_ub_action", "action_type"),
    )

    def __repr__(self) -> str:
        return f"<UserBehavior(id={self.id}, user_id={self.user_id}, action='{self.action_type}')>"


class DailyStats(Base):
    """每日运营统计表."""

    __tablename__ = "daily_stats"

    id: int = Column(Integer, primary_key=True, autoincrement=True)  # type: ignore[assignment]
    date: date = Column(Date, unique=True, nullable=False, index=True)  # type: ignore[assignment]
    dau: int = Column(Integer, default=0)  # type: ignore[assignment]
    page_views: int = Column(Integer, default=0)  # type: ignore[assignment]
    new_users: int = Column(Integer, default=0)  # type: ignore[assignment]
    crawl_count: int = Column(Integer, default=0)  # type: ignore[assignment]
    llm_cost: float = Column(Float, default=0.0)  # type: ignore[assignment]
    created_at: datetime = Column(DateTime, default=lambda: datetime.now(timezone.utc))  # type: ignore[assignment]

    def __repr__(self) -> str:
        return f"<DailyStats(id={self.id}, date={self.date}, dau={self.dau}, llm_cost=${self.llm_cost:.4f})>"
