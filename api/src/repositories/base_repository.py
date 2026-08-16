"""
Base Repository - Abstract base class for all repositories.
Implements Repository Pattern for data access layer.
"""
import logging
from typing import TypeVar, Generic, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import func

logger = logging.getLogger(__name__)

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """
    Generic base repository for CRUD operations.
    Implements Dependency Inversion Principle (abstracts database interaction).
    """

    def __init__(self, model: type[T], db: AsyncSession):
        """
        Initialize repository with model and database session.

        Args:
            model: SQLAlchemy model class
            db: Async database session
        """
        self.model = model
        self.db = db

    async def create(self, obj: T) -> T:
        """Create a new entity."""
        self.db.add(obj)
        await self.db.flush()
        return obj

    async def get_by_id(self, obj_id: int) -> Optional[T]:
        """Get entity by ID."""
        stmt = select(self.model).where(self.model.id == obj_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all entities with pagination."""
        stmt = select(self.model).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def count(self) -> int:
        """Count total entities."""
        stmt = select(func.count(self.model.id))
        result = await self.db.execute(stmt)
        return result.scalar()

    async def update(self, obj_id: int, obj_data: dict) -> Optional[T]:
        """Update an entity."""
        obj = await self.get_by_id(obj_id)
        if obj:
            for key, value in obj_data.items():
                setattr(obj, key, value)
            await self.db.flush()
        return obj

    async def delete(self, obj_id: int) -> bool:
        """Delete an entity by ID."""
        obj = await self.get_by_id(obj_id)
        if obj:
            await self.db.delete(obj)
            await self.db.flush()
            return True
        return False

    async def commit(self) -> None:
        """Commit transaction."""
        await self.db.commit()

    async def rollback(self) -> None:
        """Rollback transaction."""
        await self.db.rollback()
