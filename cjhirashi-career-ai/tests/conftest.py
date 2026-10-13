"""Fixtures compartidas. Variables mínimas ANTES de importar `config` (singleton)."""
import os

os.environ.setdefault("AI_DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/career_ai_test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-0123456789abcdef0123456789")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("API_BASE_URL", "http://api.test")
os.environ.setdefault("AI_SERVICE_TOKEN", "test-service-token")

# ---------------------------------------------------------------------------
# Postgres desechable (secuencias, tsvector, GIN). NUNCA la BD de desarrollo.
# Sin TEST_DATABASE_URL los tests que lo piden se saltan con un motivo claro.
# ---------------------------------------------------------------------------
import pytest  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # noqa: E402


@pytest.fixture(scope="session")
def pg_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip(
            "necesita Postgres real (secuencias, tsvector, GIN): exporta "
            "TEST_DATABASE_URL=postgresql+asyncpg://…/<base_desechable>"
        )
    return url


@pytest.fixture
async def pg_engine(pg_url):
    """Engine async sobre un esquema `public` recién vaciado (la base es desechable)."""
    engine = create_async_engine(pg_url, future=True)
    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
    yield engine
    await engine.dispose()


@pytest.fixture
async def pg_db(pg_engine):
    """Esquema creado desde los modelos + secuencias de IDs prefijados; devuelve la factory."""
    import models  # noqa: F401
    from database import Base
    from services.id_generator import TABLE_PREFIXES

    async with pg_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        for prefix in TABLE_PREFIXES.values():
            await conn.execute(text(f"CREATE SEQUENCE IF NOT EXISTS {prefix}_id_seq START 1"))
    return async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
