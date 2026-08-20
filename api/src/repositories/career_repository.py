"""
Generic repository for the career-domain (v2) tables.

All 30 career-domain tables share the same shape of concern: every row
belongs to exactly one user (`user_id` column) and must never be
readable/writable by another user. Rather than duplicating that
row-level-isolation logic 30 times, this generic repository implements it
once and is parametrized by the SQLAlchemy model.
"""
from typing import Generic, Optional, Sequence, Type, TypeVar

from sqlalchemy import String, Text, func as sa_func, inspect, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import Base

ModelType = TypeVar("ModelType", bound=Base)


class CareerRepository(Generic[ModelType]):
    """Generic CRUD repository enforcing per-user row-level isolation."""

    def __init__(self, model: Type[ModelType]):
        self.model = model
        # Computed once per model (not per request): every real column name
        # (for validating `sort_by`) and the string/text ones among them
        # (for the free-text `search` filter below).
        column_attrs = list(inspect(model).mapper.column_attrs)
        self._column_names = {attr.key for attr in column_attrs}
        self._text_columns = [
            attr.key for attr in column_attrs if isinstance(attr.columns[0].type, (String, Text))
        ]

    async def list_for_user(
        self,
        db: AsyncSession,
        user_id: int,
        skip: int = 0,
        limit: int = 20,
        sort_by: Optional[str] = None,
        sort_dir: str = "asc",
        search: Optional[str] = None,
    ) -> Sequence[ModelType]:
        """Return a page of rows belonging to `user_id`.

        `sort_by` defaults to newest-first (`id desc`) when absent or not a
        real column on this model - never trusted blindly, since it comes
        straight from the query string. `search` does a case-insensitive
        OR-match across every string/text column of the model.
        """
        stmt = select(self.model).where(self.model.user_id == user_id)

        if search and self._text_columns:
            like = f"%{search}%"
            stmt = stmt.where(or_(*(getattr(self.model, col).ilike(like) for col in self._text_columns)))

        if sort_by and sort_by in self._column_names:
            column = getattr(self.model, sort_by)
            stmt = stmt.order_by(column.desc() if sort_dir == "desc" else column.asc())
        else:
            stmt = stmt.order_by(self.model.id.desc())

        stmt = stmt.offset(skip).limit(limit)
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
