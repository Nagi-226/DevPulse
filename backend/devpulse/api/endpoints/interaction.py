"""用户互动 API 端点 — 评论/点赞/分享."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import delete, func, select

from devpulse.api.dependencies import get_current_user, get_optional_user
from devpulse.core.database import Database
from devpulse.core.models import Comment, Like, Repository, User, UserBehavior

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/repos", tags=["interactions"])


async def _get_repo(session: Any, full_name: str) -> Repository:
    """获取仓库，不存在则 404."""
    result = await session.execute(
        select(Repository).where(Repository.full_name == full_name)
    )
    repo = result.scalar_one_or_none()
    if repo is None:
        raise HTTPException(
            status_code=404, detail=f"Repository '{full_name}' not found"
        )
    return repo


async def _record_behavior(
    session: Any, user_id: int, repo_id: int, action_type: str, weight: float = 1.0
) -> None:
    """记录用户行为到 user_behaviors 表."""
    behavior = UserBehavior(
        user_id=user_id,
        repo_id=repo_id,
        action_type=action_type,
        weight=weight,
        created_at=datetime.now(timezone.utc),
    )
    session.add(behavior)
    await session.commit()


# ═══════════════════════════════════════════════════════════
# 评论端点
# ═══════════════════════════════════════════════════════════

@router.get("/{full_name:path}/comments")
async def get_comments(
    full_name: str,
    request: Request,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
) -> dict[str, Any]:
    """获取仓库评论列表."""
    db: Database = request.app.state.db
    async with db.get_session() as session:
        repo = await _get_repo(session, full_name)

        # 总数
        count_stmt = select(func.count()).select_from(Comment).where(
            Comment.repo_id == repo.id,
            Comment.is_deleted == False,
            Comment.parent_id.is_(None),  # 仅顶级评论
        )
        total_result = await session.execute(count_stmt)
        total = total_result.scalar() or 0

        # 分页查询
        offset = (page - 1) * page_size
        stmt = (
            select(Comment, User)
            .join(User, Comment.user_id == User.id)
            .where(
                Comment.repo_id == repo.id,
                Comment.is_deleted == False,
                Comment.parent_id.is_(None),
            )
            .order_by(Comment.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await session.execute(stmt)
        rows = result.all()

        items = []
        for comment, user in rows:
            # 统计子评论数
            replies_count_stmt = select(func.count()).select_from(Comment).where(
                Comment.parent_id == comment.id,
                Comment.is_deleted == False,
            )
            replies_result = await session.execute(replies_count_stmt)
            replies_count = replies_result.scalar() or 0

            items.append({
                "id": comment.id,
                "user_id": comment.user_id,
                "display_name": user.display_name or user.email.split("@")[0],
                "content": comment.content,
                "parent_id": comment.parent_id,
                "replies_count": replies_count,
                "created_at": comment.created_at.isoformat() if comment.created_at else None,
                "updated_at": comment.updated_at.isoformat() if comment.updated_at else None,
            })

        return {
            "code": 0,
            "message": "success",
            "data": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "items": items,
            },
        }


@router.post("/{full_name:path}/comments")
async def create_comment(
    full_name: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    """发表评论."""
    db: Database = request.app.state.db
    async with db.get_session() as session:
        repo = await _get_repo(session, full_name)

        body = await request.json()
        content = (body.get("content") or "").strip()
        parent_id = body.get("parent_id")

        if not content:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="评论内容不能为空",
            )
        if len(content) > 2000:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="评论内容不能超过 2000 字",
            )

        comment = Comment(
            user_id=current_user["user_id"],
            repo_id=repo.id,
            content=content,
            parent_id=parent_id,
            created_at=datetime.now(timezone.utc),
        )
        session.add(comment)
        await session.commit()
        await session.refresh(comment)

        # 记录行为
        await _record_behavior(
            session, current_user["user_id"], repo.id, "comment"
        )

        logger.info(
            "User %d commented on repo %s (comment_id=%d)",
            current_user["user_id"],
            full_name,
            comment.id,
        )
        return {
            "code": 0,
            "message": "success",
            "data": {
                "id": comment.id,
                "user_id": comment.user_id,
                "content": comment.content,
                "parent_id": comment.parent_id,
                "created_at": comment.created_at.isoformat() if comment.created_at else None,
            },
        }


@router.delete("/{full_name:path}/comments/{comment_id}")
async def delete_comment(
    full_name: str,
    comment_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    """删除评论（仅本人或 admin）."""
    db: Database = request.app.state.db
    async with db.get_session() as session:
        repo = await _get_repo(session, full_name)

        result = await session.execute(
            select(Comment).where(
                Comment.id == comment_id,
                Comment.repo_id == repo.id,
            )
        )
        comment = result.scalar_one_or_none()
        if comment is None:
            raise HTTPException(status_code=404, detail="评论不存在")

        # 权限检查：本人或 admin
        is_admin = False
        try:
            user_result = await session.execute(
                select(User).where(User.id == current_user["user_id"])
            )
            user_row = user_result.scalar_one_or_none()
            if user_row and getattr(user_row, "role", "user") == "admin":
                is_admin = True
        except Exception:
            pass

        if comment.user_id != current_user["user_id"] and not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权删除此评论",
            )

        # 软删除
        comment.is_deleted = True
        await session.commit()

        logger.info(
            "User %d deleted comment %d on repo %s",
            current_user["user_id"],
            comment_id,
            full_name,
        )
        return {"code": 0, "message": "success", "data": {"deleted": True}}


# ═══════════════════════════════════════════════════════════
# 点赞端点 (Toggle)
# ═══════════════════════════════════════════════════════════

@router.post("/{full_name:path}/like")
async def toggle_like(
    full_name: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    """点赞/取消赞 (Toggle)."""
    db: Database = request.app.state.db
    async with db.get_session() as session:
        repo = await _get_repo(session, full_name)

        # 检查是否已点赞
        result = await session.execute(
            select(Like).where(
                Like.user_id == current_user["user_id"],
                Like.repo_id == repo.id,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            # 取消点赞
            await session.execute(
                delete(Like).where(Like.id == existing.id)
            )
            await session.commit()

            # 统计
            count_result = await session.execute(
                select(func.count()).select_from(Like).where(Like.repo_id == repo.id)
            )
            count = count_result.scalar() or 0

            return {
                "code": 0,
                "message": "success",
                "data": {"liked": False, "count": count},
            }
        else:
            # 点赞
            like = Like(
                user_id=current_user["user_id"],
                repo_id=repo.id,
                created_at=datetime.now(timezone.utc),
            )
            session.add(like)
            await session.commit()

            # 记录行为
            await _record_behavior(
                session, current_user["user_id"], repo.id, "like", weight=0.8
            )

            count_result = await session.execute(
                select(func.count()).select_from(Like).where(Like.repo_id == repo.id)
            )
            count = count_result.scalar() or 0

            logger.info(
                "User %d liked repo %s (count=%d)",
                current_user["user_id"],
                full_name,
                count,
            )
            return {
                "code": 0,
                "message": "success",
                "data": {"liked": True, "count": count},
            }


@router.get("/{full_name:path}/likes-count")
async def get_likes_count(
    full_name: str,
    request: Request,
    current_user: dict | None = Depends(get_optional_user),
) -> dict[str, Any]:
    """获取点赞数 + 当前用户是否已点赞."""
    db: Database = request.app.state.db
    async with db.get_session() as session:
        repo = await _get_repo(session, full_name)

        count_result = await session.execute(
            select(func.count()).select_from(Like).where(Like.repo_id == repo.id)
        )
        count = count_result.scalar() or 0

        is_liked = False
        if current_user:
            like_result = await session.execute(
                select(Like).where(
                    Like.user_id == current_user["user_id"],
                    Like.repo_id == repo.id,
                )
            )
            is_liked = like_result.scalar_one_or_none() is not None

        return {
            "code": 0,
            "message": "success",
            "data": {"likes_count": count, "is_liked": is_liked},
        }


@router.get("/{full_name:path}/interactions")
async def get_interactions(
    full_name: str,
    request: Request,
) -> dict[str, Any]:
    """获取项目互动统计."""
    db: Database = request.app.state.db
    async with db.get_session() as session:
        repo = await _get_repo(session, full_name)

        # 点赞数
        likes_stmt = select(func.count()).select_from(Like).where(Like.repo_id == repo.id)
        likes_result = await session.execute(likes_stmt)
        likes_count = likes_result.scalar() or 0

        # 评论数
        comments_stmt = (
            select(func.count())
            .select_from(Comment)
            .where(Comment.repo_id == repo.id, Comment.is_deleted == False)
        )
        comments_result = await session.execute(comments_stmt)
        comments_count = comments_result.scalar() or 0

        return {
            "code": 0,
            "message": "success",
            "data": {
                "likes_count": likes_count,
                "comments_count": comments_count,
            },
        }
