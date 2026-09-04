"""feature 001: el perfil del chat contextual sale del catálogo de Secciones
del Admin (``agent_profile_id`` L2 de la sección); sin agente o sin match con
ninguna sección degrada al orquestador. Nunca lanza.
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from services import section_catalog

_ORCHESTRATOR = "agent_orchestrator"


@pytest.fixture
async def overrides_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.exec_driver_sql(
            "CREATE TABLE admin_section_overrides ("
            "section_id VARCHAR(40) PRIMARY KEY, "
            "agent_profile_id VARCHAR(50), "
            "views JSON, "
            "updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL)"
        )
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()


async def _resolve(db, route, *, surface="contextual", agent_profile_id=None):
    return await section_catalog.resolve_profile_for_turn(
        db,
        chat_surface=surface,
        agent_profile_id=agent_profile_id,
        page_context={"route": route},
    )


@pytest.mark.requisito("RF-012")
@pytest.mark.asyncio
async def test_contextual_uses_section_l2_agent(overrides_db):
    # /settings/sections → sec-17, default_agent_profile_id = agent_configuration (L2)
    profile = await _resolve(overrides_db, "/settings/sections")
    assert profile.id == "agent_configuration"
    assert profile.level == 2


@pytest.mark.requisito("RF-022")
@pytest.mark.asyncio
async def test_contextual_no_agent_falls_back_to_orchestrator(overrides_db):
    # /dashboard → sec-1, sin agente tras el re-mapeo de la feature 001
    profile = await _resolve(overrides_db, "/dashboard")
    assert profile.id == _ORCHESTRATOR


@pytest.mark.requisito("RF-022")
@pytest.mark.asyncio
async def test_contextual_unmatched_route_falls_back_to_orchestrator(overrides_db):
    profile = await _resolve(overrides_db, "/this/route/matches/no/section")
    assert profile.id == _ORCHESTRATOR


@pytest.mark.requisito("RF-020")
@pytest.mark.asyncio
async def test_contextual_no_agent_never_raises(overrides_db):
    # RF-020: nada de 5xx — devuelve un perfil válido siempre
    for route in ("/dashboard", "/files", "/tasks", "/agent/chat", "/nope"):
        profile = await _resolve(overrides_db, route)
        assert profile.level in (1, 2)


@pytest.mark.asyncio
async def test_general_surface_is_orchestrator(overrides_db):
    profile = await _resolve(overrides_db, "/dashboard", surface="general")
    assert profile.id == _ORCHESTRATOR


@pytest.mark.asyncio
async def test_explicit_request_override_wins(overrides_db):
    profile = await _resolve(
        overrides_db, "/dashboard", agent_profile_id="agent_networking"
    )
    assert profile.id == "agent_networking"
