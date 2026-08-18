"""
Generic repository for the career-domain (v2) tables.

All 30 career-domain tables share the same shape of concern: every row
belongs to exactly one user (`user_id` column) and must never be
readable/writable by another user. Rather than duplicating that
row-level-isolation logic 30 times, this generic repository implements it
once and is parametrized by the SQLAlchemy model.
"""
from typing import Generic, Optional, Sequence, Type, TypeVar

from sqlalchemy import func as sa_func
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import Base

ModelType = TypeVar("ModelType", bound=Base)


class CareerRepository(Generic[ModelType]):
    """Generic CRUD repository enforcing per-user row-level isolation."""

    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def list_for_user(
        self,
        db: AsyncSession,
        user_id: int,
        skip: int = 0,
        limit: int = 20,
    ) -> Sequence[ModelType]:
        """Return a page of rows belonging to `user_id`, newest first."""
        stmt = (
            select(self.model)
            .where(self.model.user_id == user_id)
            .order_by(self.model.id.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def count_for_user(self, db: AsyncSession, user_id: int) -> int:
        """Return the total number of rows belonging to `user_id`."""
        stmt = select(sa_func.count()).select_from(self.model).where(self.model.user_id == user_id)
        result = await db.execute(stmt)
        return result.scalar_one()

    async def get_for_user(
        self, db: AsyncSession, user_id: int, item_id: int
    ) -> Optional[ModelType]:
        """Fetch a single row by id, scoped to `user_id`. Never trusts a bare id lookup."""
        stmt = select(self.model).where(
            self.model.id == item_id, self.model.user_id == user_id
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_for_user(
        self, db: AsyncSession, user_id: int, data: dict
    ) -> ModelType:
        """
        Create a row, forcing `user_id` from the authenticated user (never
        from payload).

        Commits explicitly rather than relying on `database.get_db()`'s
        post-response commit: that commit runs *after* the HTTP response has
        already been sent to the client (it fires when the dependency's
        AsyncExitStack is closed, which happens outside the ASGI `send()`
        call), so a client issuing an immediate follow-up request can race
        the commit and see stale/missing data. Explicit commit here
        guarantees the write is durable before the response is returned.
        """
        data = dict(data)
        data.pop("user_id", None)
        obj = self.model(user_id=user_id, **data)
        db.add(obj)
        await db.flush()
        await db.refresh(obj)
        await db.commit()
        return obj

    async def update_for_user(
        self, db: AsyncSession, user_id: int, item_id: int, data: dict
    ) -> Optional[ModelType]:
        """Partially update a row scoped to `user_id`. Returns None if not found/not owned."""
        obj = await self.get_for_user(db, user_id, item_id)
        if obj is None:
            return None
        data = dict(data)
        data.pop("user_id", None)
        for key, value in data.items():
            setattr(obj, key, value)
        await db.flush()
        await db.refresh(obj)
        await db.commit()
        return obj

    async def delete_for_user(self, db: AsyncSession, user_id: int, item_id: int) -> bool:
        """Delete a row scoped to `user_id`. Returns False if not found/not owned."""
        obj = await self.get_for_user(db, user_id, item_id)
        if obj is None:
            return False
        await db.delete(obj)
        await db.commit()
        return True
