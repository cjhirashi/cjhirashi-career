"""Fixtures para la jerarquía de secciones del Admin (ADR-022).

SQLite in-memory con solo las 5 tablas nuevas (metadata acotada para esquivar el
``JSONB`` de otros modelos) + ``PRAGMA foreign_keys=ON`` para ejercitar CASCADE.
Se puebla con el seeder idempotente real.
"""
import pytest
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from models.admin_section_group import AdminSectionGroup
from models.admin_section_l1 import AdminSectionL1
from models.admin_section_l2 import AdminSectionL2
from models.admin_section_l3 import AdminSectionL3
from models.admin_view import AdminView
from services import section_catalog
from services.admin_sections_seed import sync_structure

_TABLES = [
    AdminSectionGroup.__table__,
    AdminSectionL1.__table__,
    AdminSectionL2.__table__,
    AdminSectionL3.__table__,
    AdminView.__table__,
]


@pytest.fixture
async def hier_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)

    @event.listens_for(engine.sync_engine, "connect")
    def _fk_on(dbapi_conn, _rec):  # pragma: no cover - trivial
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

    async with engine.begin() as conn:
        for table in _TABLES:
            await conn.run_sync(lambda c, t=table: t.create(c))
    yield engine
    await engine.dispose()


@pytest.fixture
async def hier_session_factory(hier_engine):
    return async_sessionmaker(hier_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture
async def hier_db(hier_session_factory):
    """Sesión ya poblada por el seeder. Invalida la caché del catálogo al empezar y terminar."""
    section_catalog.invalidate_cache()
    async with hier_session_factory() as session:
        await sync_structure(session)
        await session.commit()
    async with hier_session_factory() as session:
        yield session
    section_catalog.invalidate_cache()


@pytest.fixture
async def hier_db_empty(hier_session_factory):
    """Sesión con las tablas creadas pero SIN seed."""
    section_catalog.invalidate_cache()
    async with hier_session_factory() as session:
        yield session
    section_catalog.invalidate_cache()
