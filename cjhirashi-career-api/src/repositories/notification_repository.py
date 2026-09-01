"""
Repository for UserNotification — in-app notification management.

FASE 2: Consolidate db.execute() for notification queries.
Centralizes per-user row-level isolation and notification lifecycle.
"""
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user_notification import UserNotification


class NotificationRepository:
    """Repository for UserNotification CRUD operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.model = UserNotification

    async def list_for_user(
        self,
        user_id: str,
        unread_only: bool = False,
        limit: int = 30,
        skip: int = 0,
    ) -> List[UserNotification]:
        """List notifications for a user, optionally filtering to unread."""
        stmt = select(UserNotification).where(UserNotification.user_id == user_id)

        if unread_only:
            stmt = stmt.where(UserNotification.read_at.is_(None))

        stmt = stmt.order_by(UserNotification.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def unread_count(self, user_id: str) -> int:
        """Count unread notifications for a user."""
        stmt = (
            select(func.count())
            .select_from(UserNotification)
            .where(
                UserNotification.user_id == user_id,
                UserNotification.read_at.is_(None),
            )
        )
        result = await self.db.execute(stmt)
        return int(result.scalar() or 0)

    async def mark_all_read(self, user_id: str) -> int:
        """Mark all unread notifications as read for a user. Returns count of updated."""
        stmt = select(UserNotification).where(
            UserNotification.user_id == user_id,
            UserNotification.read_at.is_(None),
        )
        result = await self.db.execute(stmt)
        notifications = result.scalars().all()

        now = datetime.now(timezone.utc)
        count = 0
        for notification in notifications:
            notification.read_at = now
            count += 1

        await self.db.flush()
        return count

    async def mark_read(self, user_id: str, notification_id: str) -> Optional[UserNotification]:
        """Mark a specific notification as read. Returns the notification if found and updated."""
        stmt = select(UserNotification).where(
            UserNotification.id == notification_id,
            UserNotification.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        notification = result.scalar_one_or_none()

        if notification and notification.read_at is None:
            notification.read_at = datetime.now(timezone.utc)
            await self.db.flush()

        return notification

    async def create(
        self,
        user_id: str,
        kind: str,
        title: str,
        body: str,
        resource_key: Optional[str] = None,
        resource_id: Optional[str] = None,
    ) -> UserNotification:
        """Create a new notification for a user."""
        notification = UserNotification(
            user_id=user_id,
            kind=kind,
            title=title,
            body=body,
            resource_key=resource_key,
            resource_id=resource_id,
        )
        self.db.add(notification)
        await self.db.flush()
        return notification

    async def get_by_id(self, user_id: str, notification_id: str) -> Optional[UserNotification]:
        """Get a specific notification, verifying ownership."""
        stmt = select(UserNotification).where(
            UserNotification.id == notification_id,
            UserNotification.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def delete(self, user_id: str, notification_id: str) -> bool:
        """Delete a notification, verifying ownership. Returns True if deleted."""
        notification = await self.get_by_id(user_id, notification_id)
        if notification:
            await self.db.delete(notification)
            await self.db.flush()
            return True
        return False
