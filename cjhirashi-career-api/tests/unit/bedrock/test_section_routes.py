"""Rutas de secciones y guardia L2 (spec 004 — RF-003, RF-005/006, RF-014)."""
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app import app
from database import get_db
from middleware.auth import get_current_user


class _FakeUser:
    id = "usr-2"


class _FakeDB:
    async def execute(self, *a, **k):
        class _R:
            def all(_self):
                return []

            def scalar_one_or_none(_self):
                return None
        return _R()


async def _override_db():
    yield _FakeDB()


def _client():
    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_user] = lambda: _FakeUser()
    return TestClient(app)


# --- RF-003: PUT sobre un L2 -> 409 -------------------------------------------

@pytest.mark.requisito("RF-003")
def test_put_agent_tools_l2_returns_409():
    client = _client()
    try:
        resp = client.put(
            "/bedrock/agent-profiles/agent_professional_identity/tools",
            json={"tool_names": ["list_career_record"]},
        )
        assert resp.status_code == 409
        assert "sección" in resp.text.lower() or "seccion" in resp.text.lower()
    finally:
        client.close()
        app.dependency_overrides.clear()


@pytest.mark.requisito("RF-003")
def test_put_agent_methodologies_l2_returns_409():
    client = _client()
    try:
        resp = client.put(
            "/bedrock/agent-profiles/agent_professional_identity/methodologies",
            json={"methodology_ids": []},
        )
        assert resp.status_code == 409
    finally:
        client.close()
        app.dependency_overrides.clear()


@pytest.mark.requisito("RF-004")
def test_put_agent_tools_l3_still_works():
    client = _client()
    try:
        with patch(
            "services.bedrock.profile_tools.set_tool_override",
            new=AsyncMock(return_value={
                "profile_id": "agent_visual_design",
                "default_tools": [], "override_tools": ["generate_image"],
                "effective_tools": ["generate_image"], "by_section": None,
            }),
        ):
            resp = client.put(
                "/bedrock/agent-profiles/agent_visual_design/tools",
                json={"tool_names": ["generate_image"]},
            )
        assert resp.status_code == 200
    finally:
        client.close()
        app.dependency_overrides.clear()


# --- RF-005/006/014: secciones ---------------------------------------------

@pytest.mark.requisito("RF-014")
def test_get_section_returns_derived_tools_and_methodologies():
    client = _client()
    try:
        with patch(
            "services.section_catalog.get_section",
            new=AsyncMock(return_value={"agent_profile_id": "agent_professional_identity"}),
        ), patch(
            "services.section_catalog.section_methodology_ids",
            new=AsyncMock(return_value=["opm-1"]),
        ):
            resp = client.get("/bedrock/sections/sec-32")
        assert resp.status_code == 200
        body = resp.json()
        assert body["section_id"] == "sec-32"
        assert "list_career_record" in body["derived_tools"]
        assert body["methodology_ids"] == ["opm-1"]
    finally:
        client.close()
        app.dependency_overrides.clear()


@pytest.mark.requisito("RF-005")
def test_put_section_methodologies_links():
    client = _client()
    try:
        with patch(
            "services.section_catalog.set_section_methodologies",
            new=AsyncMock(return_value=["opm-1", "opm-2"]),
        ) as setter, patch(
            "services.section_catalog.get_section",
            new=AsyncMock(return_value={"agent_profile_id": None}),
        ), patch(
            "services.section_catalog.section_methodology_ids",
            new=AsyncMock(return_value=["opm-1", "opm-2"]),
        ):
            resp = client.put(
                "/bedrock/sections/sec-32/methodologies",
                json={"methodology_ids": ["opm-1", "opm-2"]},
            )
        assert resp.status_code == 200
        setter.assert_awaited_once()
        assert resp.json()["methodology_ids"] == ["opm-1", "opm-2"]
    finally:
        client.close()
        app.dependency_overrides.clear()


@pytest.mark.requisito("RF-006")
def test_put_section_methodologies_unknown_id_returns_400():
    client = _client()
    try:
        with patch(
            "services.section_catalog.set_section_methodologies",
            new=AsyncMock(side_effect=ValueError("Unknown methodology ids: ['opm-999']")),
        ):
            resp = client.put(
                "/bedrock/sections/sec-32/methodologies",
                json={"methodology_ids": ["opm-999"]},
            )
        assert resp.status_code == 400
    finally:
        client.close()
        app.dependency_overrides.clear()


@pytest.mark.requisito("RF-006")
def test_put_section_methodologies_unknown_section_returns_404():
    client = _client()
    try:
        with patch(
            "services.section_catalog.set_section_methodologies",
            new=AsyncMock(side_effect=KeyError("Unknown admin section: sec-nope")),
        ):
            resp = client.put(
                "/bedrock/sections/sec-nope/methodologies",
                json={"methodology_ids": []},
            )
        assert resp.status_code == 404
    finally:
        client.close()
        app.dependency_overrides.clear()


# --- RF-014: GET tools de un L2 trae by_section ----------------------------

@pytest.mark.requisito("RF-014")
def test_get_agent_tools_l2_has_by_section():
    client = _client()
    try:
        with patch(
            "services.section_catalog.sections_for_agent",
            new=AsyncMock(return_value=[{"id": "sec-32"}]),
        ):
            resp = client.get("/bedrock/agent-profiles/agent_professional_identity/tools")
        assert resp.status_code == 200
        body = resp.json()
        assert body["override_tools"] is None
        assert body["by_section"] and body["by_section"][0]["section_id"] == "sec-32"
        assert "list_career_record" in body["effective_tools"]
    finally:
        client.close()
        app.dependency_overrides.clear()
