"""
Configuración de pytest y fixtures compartidas para todos los tests.
"""
import pytest
import asyncio
import sys
from pathlib import Path

# Agregar el directorio src al path para importaciones
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from database import Base, get_db
from config import settings
from models import User, Identity, Competency, Evidence
from services.auth_service import AuthService


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
    Fixture que crea una base de datos de prueba en memoria.
    Retorna un engine y una session factory.
    """
    # Usar SQLite en memoria para tests
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True
    )

    # Crear todas las tablas
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Crear session factory
    TestingSessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    yield TestingSessionLocal

    # Limpiar
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
        ikigai_passion="Escribir código",
        ikigai_profession="Desarrollo de software",
        ikigai_vocation="Crear soluciones innovadoras",
        ikigai_mission="Impactar positivamente a través de la tecnología",
        key_differentiators="Experiencia en arquitectura",
        unique_value_proposition="Soluciones escalables y mantenibles"
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
    competency = Competency(
        user_id=test_user.id,
        name="Python",
        description="Desarrollo backend con Python",
        type="técnica",
        level="Expert",
        proficiency_score=95,
        years_of_experience=5,
        is_highlighted=True
    )
    db_session.add(competency)
    await db_session.flush()
    await db_session.refresh(competency)
    return competency


# ============================================================================
# EVIDENCE FIXTURES
# ============================================================================

@pytest.fixture
async def test_evidence(db_session: AsyncSession, test_user: User):
    """Crear una evidencia de prueba."""
    from datetime import date

    evidence = Evidence(
        user_id=test_user.id,
        type="project",
        title="API REST con FastAPI",
        description="Desarrollo de API REST escalable",
        company="Tech Corp",
        position="Senior Developer",
        start_date=date(2022, 1, 1),
        end_date=date(2023, 12, 31),
        url="https://github.com/example/project",
        is_featured=True,
        star_situation="Necesidad de refactorizar API legacy",
        star_task="Diseñar nueva arquitectura",
        star_action="Implementé FastAPI con SQLAlchemy",
        star_result="Mejora 40% en performance"
    )
    db_session.add(evidence)
    await db_session.flush()
    await db_session.refresh(evidence)
    return evidence


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
