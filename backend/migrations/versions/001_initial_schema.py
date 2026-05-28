"""Initial schema — users, repositories, weekly_reports, favorites, star_history

Revision ID: 001
Revises:
Create Date: 2026-05-28
"""
from alembic import op
import sqlalchemy as sa


revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """创建所有初始表."""
    # ── users 表 ───────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=True),
        sa.Column("push_enabled", sa.Boolean(), default=True),
        sa.Column("push_weekly_report", sa.Boolean(), default=True),
        sa.Column("push_important_project", sa.Boolean(), default=False),
        sa.Column("fcm_token", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("idx_users_email", "users", ["email"], unique=True)

    # ── repositories 表 ────────────────────────
    op.create_table(
        "repositories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column("owner", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("language", sa.String(length=50), nullable=True),
        sa.Column("topics", sa.JSON(), nullable=True),
        sa.Column("total_stars", sa.Integer(), default=0),
        sa.Column("stars_since", sa.Integer(), default=0),
        sa.Column("forks", sa.Integer(), default=0),
        sa.Column("forks_since", sa.Integer(), default=0),
        sa.Column("open_issues", sa.Integer(), default=0),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("url", sa.String(length=500), nullable=True),
        sa.Column("has_readme", sa.Boolean(), default=False),
        sa.Column("readme_content", sa.Text(), nullable=True),
        sa.Column("readme_summary", sa.Text(), nullable=True),
        sa.Column("key_points", sa.JSON(), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("crawled_at", sa.DateTime(), nullable=True),
        sa.Column("summarized_at", sa.DateTime(), nullable=True),
        sa.Column("trending_rank", sa.Integer(), nullable=True),
        sa.Column("trending_since", sa.String(length=20), nullable=True),
        sa.Column("source", sa.String(length=20), default="github"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("full_name"),
    )
    op.create_index("idx_repo_language", "repositories", ["language"])
    op.create_index("idx_repo_stars", "repositories", ["total_stars"])
    op.create_index("idx_repo_trending", "repositories", ["trending_rank", "trending_since"])

    # ── weekly_reports 表 ──────────────────────
    op.create_table(
        "weekly_reports",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("week_start", sa.DateTime(), nullable=False),
        sa.Column("week_end", sa.DateTime(), nullable=False),
        sa.Column("language_filter", sa.String(length=50), nullable=True),
        sa.Column("source_filter", sa.String(length=20), default="github"),
        sa.Column("total_repos", sa.Integer(), default=0),
        sa.Column("top_repos", sa.JSON(), nullable=True),
        sa.Column("overview_text", sa.Text(), nullable=True),
        sa.Column("generated_at", sa.DateTime(), nullable=True),
        sa.Column("published", sa.Boolean(), default=False),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_report_week", "weekly_reports", ["week_start"], unique=True)

    # ── favorites 表 ───────────────────────────
    op.create_table(
        "favorites",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("repo_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_fav_user_repo", "favorites", ["user_id", "repo_id"], unique=True)
    op.create_index("idx_fav_user", "favorites", ["user_id"])

    # ── star_history 表 ────────────────────────
    op.create_table(
        "star_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("repo_id", sa.Integer(), nullable=False),
        sa.Column("total_stars", sa.Integer(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_sh_repo_date", "star_history", ["repo_id", "recorded_at"])


def downgrade() -> None:
    """删除所有表."""
    op.drop_table("star_history")
    op.drop_table("favorites")
    op.drop_table("weekly_reports")
    op.drop_table("repositories")
    op.drop_table("users")
