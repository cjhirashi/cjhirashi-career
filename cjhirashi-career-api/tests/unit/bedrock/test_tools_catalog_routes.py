"""Rutas de herramientas por agente y catálogo de tools (RF-003/004/009)."""
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app import app
from database import get_db
from middleware.auth import get_current_user


class _FakeUser:
    id = "usr-1"


class _FakeScalars:
    def all(self):
        return []


class _FakeResult:
    def scalar_one_or_none(self):
        return None

    def scalars(self):
        return _FakeScalars()


class _FakeDB:
    async def execute(self, *args, **kwargs):
        return _FakeResult()

    async def commit(self):
        pass

    def add(self, obj):
        pass

    async def delete(self, obj):
        pass


async def _override_db():
    yield _FakeDB()


def _override_user():
    return _FakeUser()


def _client():
    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_user] = _override_user
    return TestClient(app)


def test_get_agent_tools_returns_state():
    # spec 004: agent_pdf_design es L2 → GET devuelve forma by_section (lectura).
    client = _client()
    try:
        with patch(
            "services.section_catalog.sections_for_agent", new=AsyncMock(return_value=[])
        ):
            resp = client.get("/bedrock/agent-profiles/agent_pdf_design/tools")
        assert resp.status_code == 200
        data = resp.json()
        assert data["override_tools"] is None
        assert data["by_section"] == []
        assert "pdf_template" in data["default_tools"]  # default de código intacto
    finally:
        client.close()
        app.dependency_overrides.clear()


def test_get_l3_agent_tools_returns_direct_state():
    client = _client()
    try:
        resp = client.get("/bedrock/agent-profiles/agent_visual_design/tools")
        assert resp.status_code == 200
        data = resp.json()
        assert data["override_tools"] is None
        assert data["by_section"] is None
        assert data["effective_tools"] == data["default_tools"]
        assert data["default_tools"]  # no vacío
    finally:
        client.close()
        app.dependency_overrides.clear()


def test_put_agent_tools_unknown_tool_returns_400():
    # L3: la validación del override sí aplica
    client = _client()
    try:
        resp = client.put(
            "/bedrock/agent-profiles/agent_visual_design/tools",
            json={"tool_names": ["not_a_tool"]},
        )
        assert resp.status_code == 400
    finally:
        client.close()
        app.dependency_overrides.clear()


def test_put_agent_tools_unknown_profile_returns_404():
    client = _client()
    try:
        resp = client.put(
            "/bedrock/agent-profiles/does_not_exist/tools",
            json={"tool_names": ["generate_image"]},
        )
        assert resp.status_code == 404
    finally:
        client.close()
        app.dependency_overrides.clear()


def test_get_tools_catalog_lists_builtin_and_mcp():
    client = _client()
    try:
        resp = client.get("/bedrock/tools/catalog")
        assert resp.status_code == 200
        data = resp.json()
        assert "builtin" in data
        assert "mcp" in data
        names = {t["name"] for t in data["builtin"]}
        assert "list_career_record" in names
        assert "search_knowledge_base" in names
    finally:
        client.close()
        app.dependency_overrides.clear()


def test_get_tools_catalog_emits_scope_per_tool():
    client = _client()
    try:
        resp = client.get("/bedrock/tools/catalog")
        assert resp.status_code == 200
        builtin = resp.json()["builtin"]
        assert all(t.get("scope") in ("section", "agent", "both") for t in builtin)
        by_name = {t["name"]: t["scope"] for t in builtin}
        # las CRUD de una tabla pertenecen a la sección
        assert by_name["create_career_record"] == "section"
        assert by_name["delete_career_record"] == "section"
        # delegación es por nivel, nunca de sección
        assert by_name["delegate_to_specialist"] == "agent"
        # search es útil en ambos
        assert by_name["search_knowledge_base"] == "both"
    finally:
        client.close()
        app.dependency_overrides.clear()
