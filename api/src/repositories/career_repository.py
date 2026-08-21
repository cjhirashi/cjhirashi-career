"""
Generic repository for the career-domain (v2) tables.

All 30 career-domain tables share the same shape of concern: every row
belongs to exactly one user (`user_id` column) and must never be
readable/writable by another user. Rather than duplicating that
row-level-isolation logic 30 times, this generic repository implements it
once and is parametrized by the SQLAlchemy model.
"""
import asyncio
import logging
from typing import Generic, Optional, Sequence, Type, TypeVar

from sqlalchemy import String, Text, func as sa_func, inspect, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import Base

ModelType = TypeVar("ModelType", bound=Base)

logger = logging.getLogger(__name__)

# Keeps a strong reference to fire-and-forget indexing tasks so they aren't
# garbage-collected mid-flight (a well-known asyncio.create_task gotcha) -
# self-removes once each task finishes, so this set never actually grows.
_background_tasks: set = set()


def _fire_and_forget(coro) -> None:
    task = asyncio.create_task(coro)
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)


class CareerRepository(Generic[ModelType]):
    """Generic CRUD repository enforcing per-user row-level isolation."""

    def __init__(self, model: Type[ModelType], resource_key: Optional[str] = None, vectorize: bool = True):
        self.model = model
        # The router-prefix form of the resource (e.g. "operational-methodologies",
        # hyphenated - matches the frontend's CAREER_RESOURCES keys and what
        # Agent Bedrock's tools use), not `model.__tablename__` (underscored).
        # Only set by `build_crud_router`; without it, indexing is skipped.
        self.resource_key = resource_key
        # False for PDF-content tables (e.g. `cv_versions`) - Carlos wants
        # the agent to read those straight from Postgres, never copied into
        # the Qdrant knowledge base. See `build_crud_router`'s `vectorize`
        # param, which is what actually sets this per resource.
        self.vectorize = vectorize
        # Computed once per model (not per request): every real column name
        # (for validating `sort_by`) and the string/text ones among them
        # (for the free-text `search` filter below).
        column_attrs = list(inspect(model).mapper.column_attrs)
        self._column_names = {attr.key for attr in column_attrs}
        self._text_columns = [
            attr.key for attr in column_attrs if isinstance(attr.columns[0].type, (String, Text))
        ]
        self._indexable_columns = [c for c in self._column_names if c not in ("id", "user_id")]

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
        # Fire-and-forget, not awaited: indexing is best-effort and can be
        # noticeably slower than the write itself (a real embedding call to
        # Bedrock over however much text the record has), so awaiting it
        # here would make the client wait - and risk a client-side timeout -
        # for something that was never allowed to fail the write anyway.
        _fire_and_forget(self._index_for_search(obj, user_id))
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
        _fire_and_forget(self._index_for_search(obj, user_id))
        return obj

    async def delete_for_user(self, db: AsyncSession, user_id: int, item_id: int) -> bool:
        """Delete a row scoped to `user_id`. Returns False if not found/not owned."""
        obj = await self.get_for_user(db, user_id, item_id)
        if obj is None:
            return False
        await db.delete(obj)
        await db.commit()
        _fire_and_forget(self._remove_from_search(item_id))
        return True

    def _record_to_text(self, obj: ModelType) -> str:
        """Flatten a record into `column: value` lines for embedding - every
        column except `id`/`user_id`, skipping empty values."""
        lines = []
        for col in self._indexable_columns:
            value = getattr(obj, col, None)
            if value not in (None, "", []):
                lines.append(f"{col}: {value}")
        return "\n".join(lines)

    async def _index_for_search(self, obj: ModelType, user_id: int) -> None:
        """Best-effort: (re)index this record in Qdrant for Agent Bedrock's
        knowledge base. Never lets an indexing failure fail the real write -
        logs and moves on. Skipped entirely if this repository wasn't built
        with a `resource_key` (see `build_crud_router`), or if `vectorize`
        is False for this resource (PDF-content tables - the agent reads
        those straight from Postgres instead)."""
        if not self.resource_key or not self.vectorize:
            return
        try:
            from services import bedrock_service, qdrant_service

            text = self._record_to_text(obj)
            if not text:
                return
            vector = await bedrock_service.embed_text(text)
            resource_type = "methodology" if self.resource_key == "operational-methodologies" else "career_record"
            await qdrant_service.upsert_point(
                user_id=user_id,
                resource_type=resource_type,
                resource_key=self.resource_key,
                record_id=obj.id,
                text=text,
                vector=vector,
            )
        except Exception:
            logger.warning(
                "Bedrock knowledge-base indexing failed for %s#%s - continuing without it",
                self.resource_key,
                getattr(obj, "id", "?"),
                exc_info=True,
            )

    async def _remove_from_search(self, item_id: int) -> None:
        """Best-effort counterpart to `_index_for_search`, called after a real delete."""
        if not self.resource_key or not self.vectorize:
            return
        try:
            from services import qdrant_service

            await qdrant_service.delete_point(resource_key=self.resource_key, record_id=item_id)
        except Exception:
            logger.warning(
                "Bedrock knowledge-base cleanup failed for %s#%s - continuing without it",
                self.resource_key,
                item_id,
                exc_info=True,
            )
