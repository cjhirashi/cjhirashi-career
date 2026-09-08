"""`admin_section_settings action=update` escribe los textos de vista (spec 004, RF-012).

El servicio `section_catalog.update_section(..., views=...)` ya persiste; aquí se
verifica que la tool lo expone.
"""
from unittest.mock import AsyncMock, patch

import pytest

from services.bedrock.tools import _run_admin_section_settings


@pytest.mark.asyncio
@pytest.mark.requisito("RF-012")
async def test_update_passes_views_to_section_catalog():
    captured = {}

    async def fake_update_section(db, section_id, *, agent_profile_id=None, clear_agent=False, views=None):
        captured["section_id"] = section_id
        captured["views"] = views
        return {"section_id": section_id, "views": views}

    with patch("services.section_catalog.update_section", new=fake_update_section):
        out = await _run_admin_section_settings(
            db=None,
            tool_input={
                "action": "update",
                "section_id": "sec-1",
                "views": {"main": {"sidebar_body": "Instrucciones nuevas de la vista."}},
            },
        )

    assert "error" not in out
    assert captured["section_id"] == "sec-1"
    assert captured["views"] == {"main": {"sidebar_body": "Instrucciones nuevas de la vista."}}


@pytest.mark.asyncio
@pytest.mark.requisito("RF-012")
async def test_update_rejects_non_object_views():
    out = await _run_admin_section_settings(
        db=None,
        tool_input={"action": "update", "section_id": "sec-1", "views": "no soy objeto"},
    )
    assert "error" in out and "views" in out["error"]


@pytest.mark.asyncio
@pytest.mark.requisito("RF-012")
async def test_update_still_accepts_agent_profile_id_alone():
    async def fake_update_section(db, section_id, *, agent_profile_id=None, clear_agent=False, views=None):
        return {"section_id": section_id, "agent_profile_id": agent_profile_id, "views": views}

    with patch("services.section_catalog.update_section", new=fake_update_section):
        out = await _run_admin_section_settings(
            db=None,
            tool_input={
                "action": "update",
                "section_id": "sec-6",
                "agent_profile_id": "agent_digital_presence",
            },
        )
    assert "error" not in out
