"""
Repository for LinkedIn-related models (LinkedInPost, LinkedInConnection, LinkedInProfile).

FASE 2: Consolidate db.execute() for LinkedIn queries.
Centralizes user isolation and LinkedIn data lifecycle.
"""
from typing import List, Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.linkedin_connection import LinkedInConnection
from models.linkedin_post import LinkedInPost
from models.linkedin_profile import LinkedInProfile


class LinkedInRepository:
    """Repository for LinkedIn models CRUD operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ========================================================================
    # LinkedInConnection operations
    # ========================================================================

    async def get_connection(self, user_id: str) -> Optional[LinkedInConnection]:
        """Get LinkedIn connection for a user."""
        stmt = select(LinkedInConnection).where(LinkedInConnection.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_or_update_connection(
        self,
        user_id: str,
        access_token: str,
        member_sub: str,
        member_name: Optional[str] = None,
        member_email: Optional[str] = None,
        profile_picture_url: Optional[str] = None,
        expires_at=None,
    ) -> LinkedInConnection:
        """Create or update a LinkedIn connection."""
        connection = await self.get_connection(user_id)
        if connection is None:
            connection = LinkedInConnection(user_id=user_id)
            self.db.add(connection)

        connection.access_token = access_token
        connection.member_sub = member_sub
        connection.member_name = member_name
        connection.member_email = member_email
        connection.profile_picture_url = profile_picture_url
        connection.expires_at = expires_at

        await self.db.flush()
        return connection

    async def delete_connection(self, user_id: str) -> bool:
        """Delete LinkedIn connection for a user."""
        connection = await self.get_connection(user_id)
        if connection:
            await self.db.delete(connection)
            await self.db.flush()
            return True
        return False

    # ========================================================================
    # LinkedInPost operations
    # ========================================================================

    async def list_posts_for_user(self, user_id: str, limit: int = 20) -> List[LinkedInPost]:
        """List LinkedIn posts for a user, most recent first."""
        stmt = (
            select(LinkedInPost)
            .where(LinkedInPost.user_id == user_id)
            .order_by(desc(LinkedInPost.created_at))
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_post(self, user_id: str, post_id: str) -> Optional[LinkedInPost]:
        """Get a LinkedIn post, verifying ownership."""
        stmt = select(LinkedInPost).where(
            LinkedInPost.id == post_id,
            LinkedInPost.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_post(
        self,
        user_id: str,
        text: str,
        status: str,
        image_url: Optional[str] = None,
        scheduled_at=None,
        linkedin_post_urn: Optional[str] = None,
        published_at=None,
    ) -> LinkedInPost:
        """Create a new LinkedIn post."""
        post = LinkedInPost(
            user_id=user_id,
            text=text,
            status=status,
            image_url=image_url,
            scheduled_at=scheduled_at,
            linkedin_post_urn=linkedin_post_urn,
            published_at=published_at,
        )
        self.db.add(post)
        await self.db.flush()
        return post

    async def update_post(
        self,
        user_id: str,
        post_id: str,
        **updates,
    ) -> Optional[LinkedInPost]:
        """Update a LinkedIn post."""
        post = await self.get_post(user_id, post_id)
        if post:
            for key, value in updates.items():
                if hasattr(post, key):
                    setattr(post, key, value)
            await self.db.flush()
        return post

    async def delete_post(self, user_id: str, post_id: str) -> bool:
        """Delete a LinkedIn post (only scheduled posts can be cancelled)."""
        post = await self.get_post(user_id, post_id)
        if post:
            await self.db.delete(post)
            await self.db.flush()
            return True
        return False

    # ========================================================================
    # LinkedInProfile operations
    # ========================================================================

    async def get_profile(self, user_id: str) -> Optional[LinkedInProfile]:
        """Get LinkedIn profile for a user."""
        stmt = select(LinkedInProfile).where(LinkedInProfile.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_or_update_profile(
        self,
        user_id: str,
        member_sub: str,
        **profile_data,
    ) -> LinkedInProfile:
        """Create or update a LinkedIn profile."""
        profile = await self.get_profile(user_id)
        if profile is None:
            profile = LinkedInProfile(user_id=user_id, member_sub=member_sub)
            self.db.add(profile)

        for key, value in profile_data.items():
            if hasattr(profile, key):
                setattr(profile, key, value)

        await self.db.flush()
        return profile
