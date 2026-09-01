"""Bandeja de avisos in-app (ADR-016). FASE 2: Centralized via NotificationRepository."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from middleware.auth import get_current_user
from models.user import User
from repositories.notification_repository import NotificationRepository
from schemas.user_notification import UnreadCountResponse, UserNotificationResponse

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=List[UserNotificationResponse], summary="Listar avisos")
async def list_notifications(
    unread: Optional[bool] = Query(None),
    limit: int = Query(30, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = NotificationRepository(db)
    return await repo.list_for_user(current_user.id, unread_only=unread is True, limit=limit)


@router.get("/unread-count", response_model=UnreadCountResponse)
async def unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = NotificationRepository(db)
    count = await repo.unread_count(current_user.id)
    return UnreadCountResponse(count=count)


@router.post("/read-all", response_model=UnreadCountResponse)
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = NotificationRepository(db)
    await repo.mark_all_read(current_user.id)
    await db.commit()
    return UnreadCountResponse(count=0)


@router.post("/{item_id}/read", response_model=UserNotificationResponse)
async def mark_read(
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = NotificationRepository(db)
    item = await repo.mark_read(current_user.id, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="aviso no encontrado")
    await db.commit()
    return item
