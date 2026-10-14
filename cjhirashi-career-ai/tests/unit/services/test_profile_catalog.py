"""RF-001 / RF-003: catálogo de perfiles; metodologías y secciones se leen por REST (cliente simulado) (T-070)."""
from contextlib import asynccontextmanager

import httpx
import pytest

from clients.sections import MethodologiesClient, SectionsClient
from services import agent_profiles as ap
from tests.unit.clients._helpers import as_user, make_api

pytestmark = pytest.mark.requisito("RF-001")

SECTIONS = [
    {"id": "sec-1", "system_name": "career-competencies", "label": "Competencias", "path": "/competencies",
     "section_type": "table", "resource_key": "competencies", "related_tools": [],
     "agent_profile_id": "agent_professional_identity"},
    {"id": "sec-2", "system_name": "agent-catalog", "label": "Catálogo", "path": "/agents",
     "section_type": "functional", "resource_key": None, "related_tools": ["agent_catalog_settings"],
     "agent_profile_id": "agent_professional_identity"},
    {"id": "sec-3", "system_name": "metrics", "label": "Métricas", "path": "/metrics",
     "section_type": "monitoring", "resource_key": None, "related_tools": [], "agent_profile_id": None},
    {"id": "sec-4", "system_name": "vacancies", "label": "Vacantes", "path": "/vacancies",
     "section_type": "table", "resource_key": "vacancies", "related_tools": [],
     "agent_profile_id": "agent_search_operations"},
]
METHODOLOGIES = [
    {"id": "met-1", "title": "Zeta compartida", "agent_profile_ids": [], "section_ids": []},
    {"id": "met-2", "title": "Alfa de soporte", "agent_profile_ids": ["agent_support"], "section_ids": []},
    {"id": "met-3", "title": "Beta de sección", "agent_profile_ids": [], "section_ids": ["sec-1"]},
    {"id": "met-4", "title": "Gamma ajena", "agent_profile_ids": ["agent_networking"], "section_ids": ["sec-4"]},
]


@asynccontextmanager
async def _session(pg_db):
    async with pg_db() as s:
        with as_user():
            yield s


def _clients():
    def handler(req: httpx.Request) -> httpx.Response:
        if req.url.path == "/admin/sections":
            return httpx.Response(200, json=SECTIONS)
        if req.url.path == "/career/operational-methodologies":
            return httpx.Response(200, json=METHODOLOGIES)
        return httpx.Response(404, json={"detail": "x"})

    api, rec = make_api(handler)
    return SectionsClient(api), MethodologiesClient(api), rec


# ----------------------------------------------------------------- applies_to_caller (puro)

def test_applies_to_caller_reglas():
    from services.profile_catalog import applies_to_caller as f

    assert f([], [], "agent_support", None) is True  # compartida
    assert f(None, None, "agent_support", None) is True
    assert f(["agent_networking"], [], "agent_methodologies", None) is True  # guardián
    assert f(["agent_networking"], [], None, None) is True  # sin caller
    assert f(["agent_support"], [], "agent_support", None) is True
    assert f(["agent_networking"], [], "agent_support", None) is False
    assert f([], ["sec-1"], "agent_professional_identity", ["sec-1", "sec-2"]) is True  # L2 por sección
    assert f([], ["sec-9"], "agent_professional_identity", ["sec-1"]) is False
    assert f("no-lista", "no-lista", "agent_support", None) is True  # basura = compartida


def test_is_shared_methodology():
    from services.profile_catalog import is_shared_methodology as f

    assert f([]) and f(None) and f("x")
    assert not f(["agent_support"])


# ----------------------------------------------------------------- tools por sección

def test_section_tools_tabla_con_resource_key_trae_el_crud_sin_search_knowledge_base():
    from services.profile_catalog import section_tools

    tools = section_tools(SECTIONS[0])
    assert {"list_career_record", "get_career_record", "create_career_record", "update_career_record",
            "delete_career_record", "bulk_update_career_record", "count_career_records",
            "describe_resource_schema"} <= tools
    assert "search_knowledge_base" not in tools


def test_section_tools_funcional_solo_related_tools_y_monitoreo_vacio():
    from services.profile_catalog import section_tools

    assert section_tools(SECTIONS[1]) == {"agent_catalog_settings"}
    assert section_tools(SECTIONS[2]) == set()
    assert section_tools({**SECTIONS[0], "resource_key": None}) == set()  # tabla sin resource_key
    assert "search_knowledge_base" not in section_tools({**SECTIONS[1], "related_tools": ["search_knowledge_base"]})


async def test_derived_tools_for_agent_une_las_secciones_que_posee():
    from services.profile_catalog import derived_tools_for_agent

    sections, _, rec = _clients()
    with as_user():
        tools = await derived_tools_for_agent(sections, "agent_professional_identity")
        none = await derived_tools_for_agent(sections, "agent_support")
    assert "agent_catalog_settings" in tools and "list_career_record" in tools
    assert none == set()
    assert {r.url.path for r in rec.requests} == {"/admin/sections"}
    assert all(r.headers["authorization"] == "Bearer user-jwt" for r in rec.requests)


async def test_resolve_effective_tools_l2_deriva_de_secciones_y_l3_usa_override(pg_db):
    from repositories import profile_repo
    from services.profile_catalog import resolve_effective_tools

    sections, _, _ = _clients()
    l2 = ap.get_profile("agent_professional_identity")
    async with _session(pg_db) as s:
        eff, ids = await resolve_effective_tools(s, sections, l2)
        assert ids == ["sec-1", "sec-2"]
        assert "delegate_to_specialist" in eff and "agent_catalog_settings" in eff

        l3 = ap.get_profile("agent_changelog")
        base, ids3 = await resolve_effective_tools(s, sections, l3)
        assert ids3 == [] and "delegate_to_specialist" not in base
        await profile_repo.set_tool_override(s, l3.id, ["list_recent_changes"])
        over, _ = await resolve_effective_tools(s, sections, l3)
        assert over == {"list_recent_changes"}


# ----------------------------------------------------------------- metodologías asignadas

async def test_list_assigned_l1_l3_por_agent_profile_ids_mas_compartidas_ordenadas_por_titulo():
    from services.profile_catalog import list_assigned_methodologies

    _, meth, rec = _clients()
    with as_user():
        got = await list_assigned_methodologies(meth, "agent_support")
    assert [m["id"] for m in got] == ["met-2", "met-1"]  # Alfa antes que Zeta
    assert got[1]["shared"] is True and got[0]["shared"] is False
    assert rec.last.url.path == "/career/operational-methodologies"


async def test_list_assigned_l2_por_secciones_y_guardian_ve_todas():
    from services.profile_catalog import list_assigned_methodologies

    _, meth, _ = _clients()
    with as_user():
        l2 = await list_assigned_methodologies(meth, "agent_professional_identity", ["sec-1"])
        guardian = await list_assigned_methodologies(meth, "agent_methodologies")
    assert [m["id"] for m in l2] == ["met-3", "met-1"]
    assert l2[0]["section_ids"] == ["sec-1"]
    assert len(guardian) == 4


# ----------------------------------------------------------------- catálogo completo

async def test_list_catalog_cruza_perfiles_secciones_metodologias_y_conversaciones(pg_db):
    from repositories import conversation_repo, profile_repo
    from services.profile_catalog import list_catalog

    sections, meth, _ = _clients()
    async with _session(pg_db) as s:
        await conversation_repo.get_or_create_conversation(s, "usr-1", "s1", "hola", agent_profile_id="agent_support")
        await profile_repo.set_prompt_suffix(s, "agent_support", "  sufijo propio  ")
        await profile_repo.set_photo(s, "agent_support", "http://f/x.png")
        items = await list_catalog(s, "usr-1", sections=sections, methodologies=meth)

    assert [i["profile_id"] for i in items] == [p.id for p in ap.list_profiles()]
    by = {i["profile_id"]: i for i in items}

    sup = by["agent_support"]
    assert sup["conversation_count"] == 1 and sup["photo_url"] == "http://f/x.png"
    assert sup["effective_suffix"] == "sufijo propio" and sup["prompt_is_default"] is False
    # paridad con la API: el catálogo mira solo agent_profile_ids, así que met-3 (solo section_ids) cuenta como compartida
    assert sup["methodology_count"] == 3
    assert {m["id"] for m in sup["assigned_methodologies"]} == {"met-1", "met-2", "met-3"}
    assert "methodologies" not in sup

    ident = by["agent_professional_identity"]
    assert [x["id"] for x in ident["sections"]] == ["sec-1", "sec-2"]
    assert ident["resource_keys"] == ["competencies"]
    assert {m["id"] for m in ident["assigned_methodologies"]} == {"met-1", "met-3"}
    assert "search_knowledge_base" not in ident["effective_tools"]

    orch = by["agent_orchestrator"]
    assert orch["delegation_is_default"] is True
    assert orch["delegation_target_ids"] == orch["default_delegation_target_ids"]
    assert all({"id", "label", "level"} == set(t) for t in orch["delegation_targets"])


async def test_list_catalog_aplica_override_de_delegacion_y_de_tools(pg_db):
    from repositories import profile_repo
    from services.profile_catalog import list_catalog

    sections, meth, _ = _clients()
    async with _session(pg_db) as s:
        await profile_repo.set_delegation_override(s, "agent_orchestrator", ["agent_support", "agent_changelog", "nope"])
        await profile_repo.set_tool_override(s, "agent_changelog", ["list_recent_changes"])
        by = {i["profile_id"]: i for i in await list_catalog(s, "usr-1", sections=sections, methodologies=meth)}
    orch = by["agent_orchestrator"]
    assert orch["delegation_is_default"] is False
    assert "agent_support" in orch["delegation_target_ids"] and "nope" not in orch["delegation_target_ids"]
    ch = by["agent_changelog"]
    assert ch["override_tools"] == ["list_recent_changes"] and ch["effective_tools"] == ["list_recent_changes"]
    assert ch["default_tools"] != ch["override_tools"]


async def test_get_catalog_item_incluye_todas_las_metodologias_con_su_asignacion(pg_db):
    from services.profile_catalog import get_catalog_item

    sections, meth, _ = _clients()
    async with _session(pg_db) as s:
        item = await get_catalog_item(s, "usr-1", "agent_support", sections=sections, methodologies=meth)
        with pytest.raises(KeyError):
            await get_catalog_item(s, "usr-1", "agent_inexistente", sections=sections, methodologies=meth)
    assert item["profile_id"] == "agent_support"
    assert {m["id"]: m["assigned"] for m in item["methodologies"]} == {
        "met-1": True, "met-2": True, "met-3": True, "met-4": False,
    }
    assert item["conversation_count"] == 0
