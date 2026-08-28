"""
Configuración de la base de datos con SQLAlchemy async.

Expone:
- `engine` — pool de conexiones async a PostgreSQL
- `AsyncSessionLocal` — factory de sesiones
- `Base` — clase base declarativa para modelos ORM
- `get_db()` — dependency FastAPI (commit/rollback automático)
- `init_db()` / `close_db()` — lifecycle en app.py
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from config import settings
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# Engine y session factory
# ============================================================================
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Session maker — una sesión por request vía get_db()
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Base declarativa — todos los modelos en models/ heredan de aquí
Base = declarative_base()


# ============================================================================
# Dependency get_db — patrón request-scoped session
# ============================================================================
async def get_db():
    """
    Dependency para obtener sesión de base de datos.
    Uso: db: AsyncSession = Depends(get_db)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


# ============================================================================
# Lifecycle helpers — llamados desde app.py lifespan
# ============================================================================
async def init_db():
    """Inicializa las tablas de la base de datos."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Prefixed IDs (`psp-1`, `idn-1`, …) need a PostgreSQL sequence per
        # table. create_all does not create them; without this, the first
        # insert on a newly added model fails with "relation *_id_seq does
        # not exist".
        from services.id_generator import TABLE_PREFIXES

        for prefix in TABLE_PREFIXES.values():
            await conn.execute(text(f"CREATE SEQUENCE IF NOT EXISTS {prefix}_id_seq START 1"))

    # ADR-022: dev/CI/tests no corren Alembic. El seeder idempotente alinea la
    # jerarquía de secciones del Admin (6 tablas) con el registro de código sin
    # tocar los campos del operador (responsible_agent_profile_id / instructions).
    from services.admin_sections_seed import sync_structure

    async with AsyncSessionLocal() as session:
        await sync_structure(session)
        await session.commit()

    logger.info("Database tables created successfully")


async def close_db():
    """Cierra las conexiones de la base de datos."""
    await engine.dispose()
    logger.info("Database connections closed")
