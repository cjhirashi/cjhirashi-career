"""
Conexión a la BD propia del harness (career_ai_db) con SQLAlchemy async.

Expone `engine`, `AsyncSessionLocal`, `Base`, `get_db()` y `close_db()`.
El esquema lo crea Alembic (alembic/versions/0001_...), no `create_all`.
"""
import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from config import settings

logger = logging.getLogger(__name__)

engine = create_async_engine(
    settings.AI_DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

Base = declarative_base()


async def get_db():
    """Dependency FastAPI: una sesión por request, commit/rollback automático."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error("Database session error: %s", e)
            raise


async def close_db() -> None:
    await engine.dispose()
