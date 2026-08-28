"""Happy-path por cada superficie re-keyeada al PK ``sec-N`` (ADR-021):
``section_catalog.set_agent_sections``, las rutas ``/admin/sections/{sec-N}`` y la
tool Bedrock ``admin_section_settings``.

Usa un engine SQLite in-memory con la tabla ``admin_section_overrides`` creada por
DDL a mano (la columna ``views`` es ``JSONB``, que SQLite no compila; mismo motivo
que ``tests/unit/bedrock/test_global_rules.py``). Solo se ejercitan campos que no
tocan ``views``.
"""
from unittest.mock import MagicMock

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from models.admin_section_override import AdminSectionOverride
from services import section_catalog
from services.bedrock.agent_profiles import AGENT_LINKEDIN_PUBLISHING, AGENT_ORCHESTRATOR
from services.bedrock.tools import _run_admin_section_settings

# linkedin-publish: su agente por defecto es AGENT_LINKEDIN_PUBLISHING, así que
# asignarla a otro perfil (el orquestador) crea de verdad una fila de override.
_SEC = "sec-6"
_SEC_SYSTEM_NAME = "linkedin-publish"


@pytest.fixture
async def overrides_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.exec_driver_sql(
            "CREATE TABLE admin_section_overrides ("
            "section_id VARCHAR(40) PRIMARY KEY, "
            "agent_profile_id VARCHAR(50), "
            "description TEXT, "
            "views JSON, "
            "updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL)"
        )
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()


# ---------------------------------------------------------------------------
# section_catalog.set_agent_sections
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_set_agent_sections_assigns_and_removes_by_sec_n(overrides_db):
    owned = await section_catalog.set_agent_sections(overrides_db, AGENT_ORCHESTRATOR, [_SEC])
    assert any(item["id"] == _SEC for item in owned)

    row = (
        await overrides_db.execute(
            select(AdminSectionOverride).where(AdminSectionOverride.section_id == _SEC)
        )
    ).scalar_one()
    assert row.agent_profile_id == AGENT_ORCHESTRATOR

    still_owned = await section_catalog.set_agent_sections(overrides_db, AGENT_ORCHESTRATOR, [])
    assert all(item["id"] != _SEC for item in still_owned)
    assert (
        await overrides_db.execute(
            select(AdminSectionOverride).where(AdminSectionOverride.section_id == _SEC)
        )
    ).scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_set_agent_sections_rejects_unknown_sec_n(overrides_db):
    with pytest.raises(KeyError):
        await section_catalog.set_agent_sections(overrides_db, AGENT_ORCHESTRATOR, ["sec-9999"])
    with pytest.raises(KeyError):
        await section_catalog.set_agent_sections(overrides_db, AGENT_ORCHESTRATOR, [_SEC_SYSTEM_NAME])


# ---------------------------------------------------------------------------
# routes/admin_sections.py — GET / PUT /admin/sections/{sec-N}
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_route_get_and_put_section_by_sec_n(overrides_db):
    from routes import admin_sections as admin_sections_routes
    from schemas.admin_sections import AdminSectionUpdateRequest

    got = await admin_sections_routes.get_admin_section(
        _SEC, current_user=MagicMock(), db=overrides_db
    )
    assert got["id"] == _SEC
    assert got["system_name"] == _SEC_SYSTEM_NAME
    assert got["description_is_default"] is True

    updated = await admin_sections_routes.update_admin_section(
        _SEC,
        AdminSectionUpdateRequest(description="Descripción curada por Carlos."),
        current_user=MagicMock(),
        db=overrides_db,
    )
    assert updated["id"] == _SEC
    assert updated["description"] == "Descripción curada por Carlos."
    assert updated["description_is_default"] is False


@pytest.mark.asyncio
async def test_route_get_unknown_sec_n_is_404(overrides_db):
    from fastapi import HTTPException

    from routes import admin_sections as admin_sections_routes

    with pytest.raises(HTTPException) as exc:
        await admin_sections_routes.get_admin_section(
            "sec-9999", current_user=MagicMock(), db=overrides_db
        )
    assert exc.value.status_code == 404


# ---------------------------------------------------------------------------
# Bedrock tool admin_section_settings
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_tool_list_exposes_pk_and_system_name(overrides_db):
    result = await _run_admin_section_settings(overrides_db, {"action": "list"})
    by_id = {item["id"]: item for item in result["items"]}
    assert by_id["sec-1"]["system_name"] == "dashboard"
    assert by_id[_SEC]["system_name"] == _SEC_SYSTEM_NAME


@pytest.mark.asyncio
async def test_tool_get_and_update_by_sec_n(overrides_db):
    got = await _run_admin_section_settings(
        overrides_db, {"action": "get", "section_id": _SEC}
    )
    assert got["item"]["id"] == _SEC

    updated = await _run_admin_section_settings(
        overrides_db,
        {"action": "update", "section_id": _SEC, "description": "Vía tool Bedrock."},
    )
    assert updated["item"]["description"] == "Vía tool Bedrock."
    assert updated["item"]["description_is_default"] is False


@pytest.mark.asyncio
async def test_tool_rejects_slug_as_section_id(overrides_db):
    result = await _run_admin_section_settings(
        overrides_db, {"action": "get", "section_id": "dashboard"}
    )
    assert "error" in result
    assert "sec-N" in result["error"]
