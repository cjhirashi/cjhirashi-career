"""Catálogo de agentes: definición de código y tools resueltas."""
import pytest
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from models.admin_section_group import AdminSectionGroup
from models.admin_section_l1 import AdminSectionL1
from models.admin_section_l2 import AdminSectionL2
from models.admin_section_l3 import AdminSectionL3
from models.admin_view import AdminView
from models.bedrock_agent_profile_photo import BedrockAgentProfilePhoto
from models.bedrock_agent_profile_prompt import BedrockAgentProfilePrompt
from models.bedrock_conversation import BedrockConversation, BedrockConversationMessage
from services import section_catalog
from services.admin_sections_seed import ensure_admin_group_and_section, sync_views
from services.bedrock.agent_profiles import (
    AGENT_CONFIGURATION,
    AGENT_ORCHESTRATOR,
    AGENT_PDF_DESIGN,
    AGENT_PDF_RENDER,
    AGENT_PROFESSIONAL_IDENTITY,
    get_profile,
    list_profiles,
)
from services.bedrock import profile_catalog
from services.bedrock.profile_catalog import resolved_tool_names, _serialize_definition

# Tablas necesarias para ejercitar list_catalog/get_catalog_item contra BD real.
# NO se incluyen bedrock_agent_delegation ni operational_methodologies: usan
# postgresql.JSONB puro (sin .with_variant) y no compilan en SQLite — problema
# preexistente y no relacionado con este lote (ver tests/unit/conftest.py). Esas
# dos lecturas se neutralizan con monkeypatch en el propio test.
_CATALOG_TABLES = [
    AdminSectionGroup.__table__,
    AdminSectionL1.__table__,
    AdminSectionL2.__table__,
    AdminSectionL3.__table__,
    AdminView.__table__,
    BedrockAgentProfilePrompt.__table__,
    BedrockAgentProfilePhoto.__table__,
    BedrockConversation.__table__,
    BedrockConversationMessage.__table__,
]


@pytest.fixture
async def catalog_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)

    @event.listens_for(engine.sync_engine, "connect")
    def _fk_on(dbapi_conn, _rec):  # pragma: no cover - trivial
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

    async with engine.begin() as conn:
        for table in _CATALOG_TABLES:
            await conn.run_sync(lambda c, t=table: t.create(c))
    yield engine
    await engine.dispose()


@pytest.fixture
async def catalog_session_factory(catalog_engine):
    return async_sessionmaker(catalog_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture
async def catalog_db(catalog_session_factory):
    """Sesión con la jerarquía de secciones sembrada por el seeder real."""
    section_catalog.invalidate_cache()
    async with catalog_session_factory() as session:
        await ensure_admin_group_and_section(session)
        await sync_views(session)
        await session.commit()
    async with catalog_session_factory() as session:
        yield session
    section_catalog.invalidate_cache()


@pytest.fixture(autouse=True)
def _stub_jsonb_only_reads(monkeypatch):
    """Neutraliza lecturas que dependen de tablas con JSONB puro (no-SQLite)."""

    async def _no_delegation_overrides(db):
        return {}

    async def _no_methodology_rows(db, user_id):
        return []

    monkeypatch.setattr(
        profile_catalog.profile_delegation, "_overrides_map", _no_delegation_overrides
    )
    monkeypatch.setattr(profile_catalog, "_methodology_rows", _no_methodology_rows)


def test_get_profile_accepts_catalog_record_id():
    from services.bedrock.agent_profiles import agent_record_id

    assert get_profile("agent-1").id == AGENT_ORCHESTRATOR
    assert get_profile(AGENT_ORCHESTRATOR).id == AGENT_ORCHESTRATOR
    profiles = list_profiles()
    assert len(profiles) >= 18
    record_ids = {agent_record_id(p.id) for p in profiles}
    assert len(record_ids) == len(profiles)
    assert all(item.startswith("agent-") for item in record_ids)


def test_orchestrator_tools_are_delegate_only():
    tools = resolved_tool_names(get_profile(AGENT_ORCHESTRATOR))
    assert tools == ["delegate_to_specialist"]


def test_identity_has_career_crud_and_search():
    tools = resolved_tool_names(get_profile(AGENT_PROFESSIONAL_IDENTITY))
    assert "list_career_record" in tools
    assert "search_knowledge_base" in tools
    assert "delegate_to_specialist" in tools
    assert "generate_pdf" not in tools


def test_pdf_render_has_no_own_memory_or_tables():
    profile = get_profile(AGENT_PDF_RENDER)
    meta = {
        "default_suffix": profile.system_prompt_suffix,
        "override_suffix": None,
        "effective_suffix": profile.system_prompt_suffix,
        "is_default": True,
    }
    item = _serialize_definition(profile, meta)
    assert item["id"] == "agent-9"
    assert item["photo_url"] is None
    assert item["system_name"] == AGENT_PDF_RENDER
    assert item["profile_id"] == AGENT_PDF_RENDER
    assert item["has_own_memory"] is False
    assert item["user_facing"] is False
    assert "generate_pdf" in item["tools"]
    assert item["prompt_is_default"] is True


def test_pdf_design_lists_template_tables():
    profile = get_profile(AGENT_PDF_DESIGN)
    meta = {
        "default_suffix": "x",
        "override_suffix": "custom",
        "effective_suffix": "custom",
        "is_default": False,
    }
    item = _serialize_definition(profile, meta, "https://files.example/agent.png")
    assert item["photo_url"] == "https://files.example/agent.png"
    assert item["system_name"] == AGENT_PDF_DESIGN
    assert "pdf-output-templates" in item["resource_keys"]
    assert "pdf-template-styles" in item["resource_keys"]
    assert item["prompt_is_default"] is False
    assert item["has_own_memory"] is True
    assert item["views"] == []


# ============================================================================
# list_catalog / get_catalog_item contra BD real (SQLite in-memory) — ADR-023
# ============================================================================

async def _assign_view_to_configuration_agent(catalog_db) -> str:
    """Toma la primera vista sembrada y la asigna al L2 agent_configuration."""
    row = (await catalog_db.execute(select(AdminView).order_by(AdminView.id))).scalars().first()
    assert row is not None, "el seeder debería haber sembrado al menos una vista"
    row.responsible_agent_profile_id = AGENT_CONFIGURATION
    await catalog_db.commit()
    return row.id


@pytest.mark.asyncio
async def test_list_catalog_attaches_owned_views_to_the_responsible_agent(catalog_db):
    view_id = await _assign_view_to_configuration_agent(catalog_db)

    items = await profile_catalog.list_catalog(catalog_db, "usr-test")

    by_id = {item["profile_id"]: item for item in items}
    config_item = by_id[AGENT_CONFIGURATION]
    assert len(config_item["views"]) == 1
    view = config_item["views"][0]
    assert view["id"] == view_id
    assert set(view.keys()) == {
        "id",
        "key",
        "label",
        "section_id",
        "section_system_name",
        "section_path",
        "data_source",
        "resource_key",
    }
    assert view["section_id"].startswith("s1-")
    assert view["section_system_name"]
    assert view["section_path"]

    # Otros perfiles no dueños de ninguna vista no traen nada.
    other_item = by_id[AGENT_ORCHESTRATOR]
    assert other_item["views"] == []


@pytest.mark.asyncio
async def test_list_catalog_derives_resource_keys_from_owned_views_with_resource_key(catalog_db):
    view_id = await _assign_view_to_configuration_agent(catalog_db)
    row = (
        await catalog_db.execute(select(AdminView).where(AdminView.id == view_id))
    ).scalar_one()
    row.data_source = "crud"
    row.resource_key = "widgets"
    await catalog_db.commit()

    items = await profile_catalog.list_catalog(catalog_db, "usr-test")
    config_item = next(item for item in items if item["profile_id"] == AGENT_CONFIGURATION)

    assert config_item["views"][0]["resource_key"] == "widgets"
    assert config_item["resource_keys"] == ["widgets"]


@pytest.mark.asyncio
async def test_list_catalog_without_owned_views_falls_back_to_profile_resource_keys(catalog_db):
    items = await profile_catalog.list_catalog(catalog_db, "usr-test")
    pdf_design_item = next(item for item in items if item["profile_id"] == AGENT_PDF_DESIGN)

    # Sin vistas propias, resource_keys conserva el default del perfil de código.
    assert pdf_design_item["views"] == []
    assert "pdf-output-templates" in pdf_design_item["resource_keys"]


@pytest.mark.asyncio
async def test_get_catalog_item_returns_only_views_owned_by_that_profile(catalog_db):
    view_id = await _assign_view_to_configuration_agent(catalog_db)

    item = await profile_catalog.get_catalog_item(catalog_db, "usr-test", AGENT_CONFIGURATION)

    assert item["profile_id"] == AGENT_CONFIGURATION
    assert len(item["views"]) == 1
    assert item["views"][0]["id"] == view_id
    # get_catalog_item incluye el detalle completo de metodologías (include_all=True).
    assert "methodologies" in item
    assert item["methodology_count"] == 0
    assert item["assigned_methodologies"] == []


@pytest.mark.asyncio
async def test_get_catalog_item_for_unrelated_profile_has_no_views(catalog_db):
    await _assign_view_to_configuration_agent(catalog_db)

    item = await profile_catalog.get_catalog_item(catalog_db, "usr-test", AGENT_ORCHESTRATOR)

    assert item["views"] == []
    assert item["resource_keys"] is None
