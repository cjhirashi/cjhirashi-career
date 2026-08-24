"""
User Repository - Data access for User entities.
Handles all user database operations.
"""
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.user import User
from repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository[User]):
    """User repository for database operations."""

    def __init__(self, db: AsyncSession):
        """Initialize user repository."""
        super().__init__(User, db)

    async def get_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username.

        Args:
            username: Username to search for

        Returns:
            User object if found, None otherwise
        """
        stmt = select(User).where(User.username == username)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email.

        Args:
            email: Email to search for

        Returns:
            User object if found, None otherwise
        """
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def user_exists(self, username: str, email: str) -> bool:
        """
        Check if user exists by username or email.

        Args:
            username: Username to check
            email: Email to check

        Returns:
            True if user exists, False otherwise
        """
        stmt = select(User).where(
            (User.username == username) | (User.email == email)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def update_last_login(self, user_id: str) -> Optional[User]:
        """
        Update user's last login timestamp.

        Args:
            user_id: User ID to update

        Returns:
            Updated user object
        """
        from datetime import datetime, timezone

        user = await self.get_by_id(user_id)
        if user:
            user.last_login = datetime.now(timezone.utc)
            await self.db.flush()
        return user

    async def get_active_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        """
        Get active users (is_active=True).

        Args:
            skip: Pagination offset
            limit: Pagination limit

        Returns:
            List of active users
        """
        stmt = (
            select(User)
            .where(User.is_active == True)
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def deactivate_user(self, user_id: str) -> Optional[User]:
        """
        Deactivate a user.

        Args:
            user_id: User ID to deactivate

        Returns:
            Updated user object
        """
        user = await self.get_by_id(user_id)
        if user:
            user.is_active = False
            await self.db.flush()
        return user

    async def activate_user(self, user_id: str) -> Optional[User]:
        """
        Activate a user.

        Args:
            user_id: User ID to activate

        Returns:
            Updated user object
        """
        user = await self.get_by_id(user_id)
        if user:
            user.is_active = True
            await self.db.flush()
        return user
