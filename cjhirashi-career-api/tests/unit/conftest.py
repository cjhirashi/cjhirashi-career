"""Fixtures para la jerarquía de secciones del Admin (ADR-022; ADR-023 corrección).

SQLite in-memory con solo las 5 tablas nuevas (metadata acotada para esquivar el
``JSONB`` de otros modelos) + ``PRAGMA foreign_keys=ON`` para ejercitar CASCADE.

Desde ADR-023 (corrección), grupos y secciones L1/L2/L3 de contenido son 100%
Admin — el código de producción ya NO los siembra (solo el grupo/sección
protegidos ``admin``, vía ``ensure_admin_group_and_section``). Para que los
~30 tests existentes (escritos contra el universo histórico de 11 grupos + 54
secciones) sigan funcionando sin reescritura masiva, ``hier_db`` reproduce ese
seed histórico **aquí, en el harness de test** (``_seed_legacy_groups_and_sections``)
y encima corre el seeder real (``ensure_admin_group_and_section`` + ``sync_views``).
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
from services.admin_sections import GROUPS, list_section_specs
from services.admin_sections_seed import ensure_admin_group_and_section, sync_views

_TABLES = [
    AdminSectionGroup.__table__,
    AdminSectionL1.__table__,
    AdminSectionL2.__table__,
    AdminSectionL3.__table__,
    AdminView.__table__,
]


async def _seed_legacy_groups_and_sections(session) -> None:
    """Reproduce el seed histórico de ADR-022 (11 grupos + 54 secciones L1) para
    que los tests existentes (escritos contra ese universo) sigan viendo el
    mismo estado. Desde ADR-023 (corrección) esto ya NO lo hace el código de
    producción (grupos/secciones de contenido son 100% Admin) — vive solo aquí,
    en el harness de test.
    """
    group_by_system = {}
    for gid, system_name, name, sort_order in GROUPS:
        session.add(
            AdminSectionGroup(
                id=gid,
                system_name=system_name,
                name=name,
                sort_order=sort_order,
                origin="code",
            )
        )
        group_by_system[system_name] = gid
    await session.flush()

    group_id_by_name = {name: gid for gid, _sys, name, _so in GROUPS}
    for spec in list_section_specs():
        session.add(
            AdminSectionL1(
                id=spec.id,
                group_id=group_id_by_name[spec.group],
                system_name=spec.system_name,
                label=spec.label,
                path=spec.path,
                section_type=spec.section_type,
                sort_order=spec.sort_order,
                origin="code",
            )
        )
    await session.flush()


async def _seed_full(session) -> None:
    """Universo completo: 11+1 grupos, 54+1 secciones, 123 vistas de código."""
    await _seed_legacy_groups_and_sections(session)
    await ensure_admin_group_and_section(session)
    await sync_views(session)


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
    """Sesión poblada con el universo histórico completo (§ ``_seed_full``).

    Invalida la caché del catálogo al empezar y terminar.
    """
    section_catalog.invalidate_cache()
    async with hier_session_factory() as session:
        await _seed_full(session)
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


@pytest.fixture
async def hier_db_bare(hier_session_factory):
    """Sesión con SOLO el grupo/sección protegidos `admin` (sin los 65 de
    contenido) — universo mínimo para tests de CRUD de grupos/secciones nuevos
    sin el ruido de las 54 secciones históricas.
    """
    section_catalog.invalidate_cache()
    async with hier_session_factory() as session:
        await ensure_admin_group_and_section(session)
        await session.commit()
    async with hier_session_factory() as session:
        yield session
    section_catalog.invalidate_cache()
