"""
Configuración de pytest y fixtures compartidas para todos los tests.
"""
import pytest
import asyncio
import os
import sys
from pathlib import Path

# Agregar el directorio src al path para importaciones
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.compiler import compiles
from httpx import AsyncClient, ASGITransport
from database import Base, get_db
from config import settings
from models import User, Identity, Competency
from services.auth_service import AuthService
from app import app


# Los modelos usan ``postgresql.JSONB`` (columna nativa de Postgres). El fixture
# ``test_db`` puede levantar SQLite in-memory, cuyo compilador no sabe renderizar
# JSONB y rompería ``Base.metadata.create_all`` para toda la suite. Este shim lo
# mapea a ``JSON`` sólo en SQLite; en Postgres no aplica.
@compiles(JSONB, "sqlite")
def _compile_jsonb_as_json_on_sqlite(element, compiler, **kw):  # noqa: ANN001
    return "JSON"


# Si ``TEST_DATABASE_URL`` apunta a un Postgres (base de datos **desechable**,
# nunca la de dev), ``test_db`` la usa: es la única forma de ejercitar los tests
# que dependen de secuencias de IDs prefijados (``usr-1``, ``psp-1``…), que
# SQLite no emula. Sin la variable, se usa SQLite in-memory (comportamiento
# histórico) y esos tests se saltan (ver `pytestmark` en test_database/
# test_middleware/test_repositories).
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
USING_POSTGRES_TEST_DB = bool(TEST_DATABASE_URL)


async def _create_prefix_sequences(conn):
    """`create_all` no crea las secuencias de IDs prefijados — igual que `init_db`."""
    from sqlalchemy import text
    from services.id_generator import TABLE_PREFIXES

    for prefix in TABLE_PREFIXES.values():
        await conn.execute(text(f"CREATE SEQUENCE IF NOT EXISTS {prefix}_id_seq START 1"))


# Fixtures que necesitan un backend real de Postgres (esquema + secuencias de
# IDs prefijados). Sin ``TEST_DATABASE_URL`` el backend es SQLite y estos tests
# no pueden pasar (no hay ``nextval``): se saltan con un motivo accionable en
# vez de romper la compuerta.
_PG_ONLY_FIXTURES = {"test_db", "db_session", "test_user", "test_identity", "test_competency"}


def pytest_collection_modifyitems(config, items):
    if USING_POSTGRES_TEST_DB:
        return
    skip_pg = pytest.mark.skip(
        reason="necesita Postgres (esquema + secuencias de IDs prefijados). "
        "Exporta TEST_DATABASE_URL=postgresql+asyncpg://…/<db_desechable> para correrlo."
    )
    for item in items:
        if _PG_ONLY_FIXTURES & set(getattr(item, "fixturenames", ())):
            item.add_marker(skip_pg)


# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Crear event loop para tests async."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_db():
    """
    Base de datos de prueba. Postgres desechable si ``TEST_DATABASE_URL`` está
    definida (ejercita secuencias de IDs prefijados); si no, SQLite in-memory.
    Retorna una session factory. Crea el esquema al entrar y lo tira al salir.
    """
    url = TEST_DATABASE_URL or "sqlite+aiosqlite:///:memory:"
    engine = create_async_engine(url, echo=False, future=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        if USING_POSTGRES_TEST_DB:
            await _create_prefix_sequences(conn)

    TestingSessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    yield TestingSessionLocal

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session(test_db):
    """Fixture que retorna una sesión de base de datos para un test."""
    async with test_db() as session:
        yield session
        await session.rollback()


# ============================================================================
# USER FIXTURES
# ============================================================================

@pytest.fixture
async def test_user(db_session: AsyncSession):
    """Crear un usuario de prueba."""
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=AuthService.hash_password("TestPassword123!"),
        full_name="Test User",
        professional_title="Software Engineer",
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_user_data():
    """Datos para crear un nuevo usuario."""
    return {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "NewPassword123!",
        "full_name": "New User",
        "professional_title": "Developer"
    }


# ============================================================================
# IDENTITY FIXTURES
# ============================================================================

@pytest.fixture
async def test_identity(db_session: AsyncSession, test_user: User):
    """Crear una identidad de prueba."""
    identity = Identity(
        user_id=test_user.id,
        passion="Escribir código",
        profession="Desarrollo de software",
        vocation="Crear soluciones innovadoras",
        mission="Impactar positivamente a través de la tecnología",
        key_strengths="Experiencia en arquitectura",
        unique_value_prop="Soluciones escalables y mantenibles"
    )
    db_session.add(identity)
    await db_session.flush()
    await db_session.refresh(identity)
    return identity


# ============================================================================
# COMPETENCY FIXTURES
# ============================================================================

@pytest.fixture
async def test_competency(db_session: AsyncSession, test_user: User):
    """Crear una competencia de prueba."""
    from models.competencies import CompetencyType, CompetencyLevel
    competency = Competency(
        user_id=test_user.id,
        name="Python",
        description="Desarrollo backend con Python",
        competency_type=CompetencyType.TECHNICAL,
        proficiency_level=CompetencyLevel.EXPERT,
        proficiency_score=95,
        years_of_experience=5,
        is_featured=True
    )
    db_session.add(competency)
    await db_session.flush()
    await db_session.refresh(competency)
    return competency


# ============================================================================
# AUTHENTICATION FIXTURES
# ============================================================================

@pytest.fixture
def valid_login_credentials():
    """Credenciales válidas para login."""
    return {
        "username": "testuser",
        "password": "TestPassword123!"
    }


@pytest.fixture
def invalid_login_credentials():
    """Credenciales inválidas para login."""
    return {
        "username": "testuser",
        "password": "WrongPassword"
    }


@pytest.fixture
def valid_jwt_token(test_user: User):
    """Crear un JWT válido para un usuario de prueba."""
    token, _ = AuthService.create_access_token(
        data={"sub": str(test_user.id)}
    )
    return token


# ============================================================================
# HTTP CLIENT FIXTURES
# ============================================================================

@pytest.fixture
async def async_client():
    """Fixture para cliente HTTP async para testing de endpoints."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client
