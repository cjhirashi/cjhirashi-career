"""Fixtures compartidas. Variables mínimas ANTES de importar `config` (singleton)."""
import os

# Aislamiento (corre al importar conftest, ANTES de que cualquier test importe `config` y se
# construya el singleton `settings`):
#  1. Ningún `.env` (del cwd, de la raíz del repo o pasado con `_env_file=`) puede leerse: el de la
#     raíz tiene credenciales reales de AWS y los tests nunca deben cargarlas.
#  2. Se descartan las variables AWS_*/BEDROCK_* heredadas del entorno.
#  3. Las variables mínimas se FIJAN (no setdefault) para que un entorno real no se cuele.
from pydantic_settings.sources import DotEnvSettingsSource  # noqa: E402

DotEnvSettingsSource._read_env_files = lambda self, *args, **kwargs: {}  # type: ignore[method-assign]

_ISOLATED_PREFIXES = ("AWS_", "BEDROCK_")
for _name in [k for k in os.environ if k.startswith(_ISOLATED_PREFIXES)]:
    del os.environ[_name]

os.environ["AI_DATABASE_URL"] = "postgresql+asyncpg://test:test@localhost:5432/career_ai_test"
os.environ["SECRET_KEY"] = "test-secret-key-0123456789abcdef0123456789"
os.environ["ALGORITHM"] = "HS256"
os.environ["API_BASE_URL"] = "http://api.test"
os.environ["AI_SERVICE_TOKEN"] = "test-service-token"

# ---------------------------------------------------------------------------
# Postgres desechable (secuencias, tsvector, GIN). NUNCA la BD de desarrollo.
# Sin TEST_DATABASE_URL los tests que lo piden se saltan con un motivo claro.
# ---------------------------------------------------------------------------
import pytest  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # noqa: E402


@pytest.fixture(autouse=True)
def _isolated_environment(monkeypatch):
    """Por test: sin AWS_*/BEDROCK_* en el entorno y sin clientes boto3 cacheados (antes y después)."""
    for name in [k for k in os.environ if k.startswith(_ISOLATED_PREFIXES)]:
        monkeypatch.delenv(name)
    from providers.bedrock import client as bedrock_client

    bedrock_client.reset_clients()
    yield
    bedrock_client.reset_clients()


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
        # D-29: la migración 0001 crea la configuración FTS; aquí (create_all) se replica.
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS unaccent"))
        await conn.execute(text("CREATE TEXT SEARCH CONFIGURATION spanish_unaccent (COPY = pg_catalog.spanish)"))
        await conn.execute(text(
            "ALTER TEXT SEARCH CONFIGURATION spanish_unaccent "
            "ALTER MAPPING FOR hword, hword_part, word WITH unaccent, spanish_stem"))
        await conn.run_sync(Base.metadata.create_all)
        for prefix in TABLE_PREFIXES.values():
            await conn.execute(text(f"CREATE SEQUENCE IF NOT EXISTS {prefix}_id_seq START 1"))
    return async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
