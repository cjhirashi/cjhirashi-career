"""Bandeja de avisos in-app (ADR-016)."""
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from middleware.auth import get_current_user
from models.user import User
from models.user_notification import UserNotification
from schemas.user_notification import UnreadCountResponse, UserNotificationResponse

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=List[UserNotificationResponse], summary="Listar avisos")
async def list_notifications(
    unread: Optional[bool] = Query(None),
    limit: int = Query(30, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(UserNotification).where(UserNotification.user_id == current_user.id)
    if unread is True:
        stmt = stmt.where(UserNotification.read_at.is_(None))
    stmt = stmt.order_by(UserNotification.created_at.desc()).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/unread-count", response_model=UnreadCountResponse)
async def unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(func.count())
        .select_from(UserNotification)
        .where(UserNotification.user_id == current_user.id, UserNotification.read_at.is_(None))
    )
    result = await db.execute(stmt)
    return UnreadCountResponse(count=int(result.scalar() or 0))


@router.post("/read-all", response_model=UnreadCountResponse)
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserNotification).where(
            UserNotification.user_id == current_user.id, UserNotification.read_at.is_(None)
        )
    )
    now = datetime.now(timezone.utc)
    for item in result.scalars().all():
        item.read_at = now
    await db.commit()
    return UnreadCountResponse(count=0)


@router.post("/{item_id}/read", response_model=UserNotificationResponse)
async def mark_read(
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserNotification).where(
            UserNotification.id == item_id, UserNotification.user_id == current_user.id
        )
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="aviso no encontrado")
    if item.read_at is None:
        item.read_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(item)
    return item
