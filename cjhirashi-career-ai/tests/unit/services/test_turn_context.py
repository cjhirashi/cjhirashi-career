"""RF-005 / D-10 / D-31 / D-32: composición REAL del turno (`agent_loop.resolve_turn_context`, T-085a).

Traslado fiel de `cjhirashi-career-api/src/services/bedrock/prompt.py:246-289` (`compose_system_prompt`: bloque de
metodologías asignadas, memoria propia sólo de `user_facing`, delegados) y de
`methodology_scope.list_assigned_methodologies`, más la derivación de tools efectivas (L2 por sus secciones).
Aquí NO se sustituye `resolve_turn_context` (lo hace `test_agent_loop.py`); se dobla lo de alrededor:
`SectionsClient`, `MethodologiesClient`, los repos y el proveedor.

`/admin/sections` trae `label`: `AdminSectionItem.label: str` (api `schemas/admin_sections.py`) y
`section_catalog.list_sections` lo rellena (`"label": spec.label`). El cliente devuelve el JSON tal cual.

INTERFAZ NUEVA QUE T-085b DEBE CUMPLIR (aditiva; compatible con los 146 tests de T-084, que no se tocan)
-----------------------------------------------------------------------------------------------------
    async def resolve_turn_context(db, user_id, profile, req, *, sections, methodologies=None) -> TurnContext
    async def chat_stream(db, user_id, req, *, provider, tool_executor, sections=None, methodologies=None, ...)
    async def run_single_turn_sync(db, *, ..., sections=None, methodologies=None, ...)
    @dataclass TurnContext(..., profile: Optional[AgentProfile] = None)

  * `methodologies`: `clients.sections.MethodologiesClient` (o doble con `async list()`), con la credencial del
    LLAMANTE (D-10: viaja por `contextvars` como el resto de clientes). `None` (valor por defecto) = no hay
    catálogo: `assigned=[]` y NO se lee nada (es lo que hacen hoy los tests de T-084).
  * Compatibilidad con T-084: sus dobles de `resolve_turn_context` sólo aceptan `(db, user_id, profile, req, *,
    sections)`. Por eso `chat_stream` pasa `methodologies=` a `resolve_turn_context` SÓLO cuando no es `None`
    (test `test_chat_stream_hands_the_methodologies_client_to_the_resolver`).
  * `TurnContext.profile` (por defecto `None` = "el que se pasó"): perfil EFECTIVO del turno. Si un L2 necesita
    leer las secciones (tools efectivas) y la lectura falla (D-31/D-32), el contexto se compone para el
    orquestador y `ctx.profile` es el orquestador; `chat_stream` adopta `ctx.profile` (modelo, historial,
    `caller_profile_id` de las tools) y el resultado del turno es el de un turno del orquestador.
  * Metodologías: `profile_catalog.list_assigned_methodologies(methodologies, profile.id, caller_section_ids)`
    → `prompt.compose_system_prompt(..., assigned=...)`, una lectura por turno. Un fallo de esa lectura se
    registra como WARNING y el turno sigue sin catálogo (como el `try/except` de la API :253-261).
  * `section_labels = {s["id"]: s["label"]}` del MISMO listado de secciones que ya se leyó (nunca una segunda
    lectura); si el turno no leyó secciones (L1/L3, `general`), no hay etiquetas.
  * D-32: `SectionsClient.list()` como máximo UNA vez por turno, perezosa y reutilizada entre la resolución del
    perfil por ruta y las tools de un L2; se cuenta en `FakeSections.list_calls`. Un fallo se registra una sola
    vez (un WARNING) y degrada a `agent_orchestrator`, también con `agent_profile_id` explícito L2.
"""
import importlib
import logging
from contextlib import asynccontextmanager
from types import SimpleNamespace
from typing import Any, List, Optional

import httpx
import pytest

from clients.api_client import ApiError
from providers.base import ToolSpec
from services import agent_profiles, profile_catalog, tools_registry
from tests.unit.services.test_agent_loop import (
    HAIKU,
    FakeDb,
    FakeProvider,
    Recorder,
    text_reply,
)

pytestmark = pytest.mark.requisito("RF-005")

ORCH = "agent_orchestrator"
L2_NETWORKING = "agent_networking"            # L2 con secciones sec-7 / sec-8
L2_IDENTITY = "agent_professional_identity"   # L2 con secciones sec-1 / sec-2
L3_CHANGELOG = "agent_changelog"              # L3 (no user_facing)

SECTIONS = [
    {"id": "sec-1", "system_name": "career-competencies", "label": "Competencias", "path": "/competencies",
     "section_type": "table", "resource_key": "competencies", "related_tools": [],
     "agent_profile_id": L2_IDENTITY},
    {"id": "sec-2", "system_name": "agent-catalog", "label": "Catálogo", "path": "/agents",
     "section_type": "functional", "resource_key": None, "related_tools": ["generate_image"],
     "agent_profile_id": L2_IDENTITY},
    {"id": "sec-4", "system_name": "vacancies", "label": "Vacantes", "path": "/vacancies",
     "section_type": "table", "resource_key": "vacancies", "related_tools": [],
     "agent_profile_id": "agent_search_operations"},
    {"id": "sec-7", "system_name": "networking", "label": "Networking", "path": "/networking",
     "section_type": "table", "resource_key": "contacts", "related_tools": [],
     "agent_profile_id": L2_NETWORKING},
    {"id": "sec-8", "system_name": "network-map", "label": "Mapa de red", "path": "/networking/map",
     "section_type": "functional", "resource_key": None, "related_tools": ["web_search"],
     "agent_profile_id": L2_NETWORKING},
    {"id": "sec-9", "system_name": "dashboard", "label": "Panel", "path": "/dashboard", "section_type": "monitoring",
     "resource_key": None, "related_tools": [], "agent_profile_id": None},
]

METHODOLOGIES = [
    {"id": "met-1", "title": "Zeta compartida", "agent_profile_ids": [], "section_ids": []},
    {"id": "met-2", "title": "Alfa del orquestador", "agent_profile_ids": [ORCH], "section_ids": []},
    {"id": "met-3", "title": "Beta de Competencias", "agent_profile_ids": [], "section_ids": ["sec-1"]},
    {"id": "met-4", "title": "Gamma ajena", "agent_profile_ids": ["agent_support"], "section_ids": ["sec-4"]},
    {"id": "met-5", "title": "Delta de Catálogo y Competencias", "agent_profile_ids": [],
     "section_ids": ["sec-2", "sec-1"]},
    {"id": "met-6", "title": "Epsilon de Networking", "agent_profile_ids": [], "section_ids": ["sec-7"]},
    {"id": "met-7", "title": "Eta de Mapa", "agent_profile_ids": [], "section_ids": ["sec-8"]},
    {"id": "met-8", "title": "Theta del bitácora", "agent_profile_ids": [L3_CHANGELOG], "section_ids": []},
]

MEMORY_NOTES = [{"id": 1, "text": "Carlos prefiere respuestas cortas"}, {"id": 2, "text": "Evita jerga"}]
FAILURES = [
    (httpx.ConnectError("sin red"), "sin red"),
    (ApiError(401, "token inválido"), "API 401"),
    (ApiError(403, "prohibido"), "API 403"),
    (ApiError(500, "boom"), "API 500"),
]


# ---------------------------------------------------------------------------------------------
# Dobles
# ---------------------------------------------------------------------------------------------
class FakeSections:
    """`SectionsClient` doble: cuenta las lecturas de `/admin/sections`."""

    def __init__(self, items=None, fail=None):
        self.items = SECTIONS if items is None else items
        self.fail = fail
        self.list_calls = 0

    async def list(self):
        self.list_calls += 1
        if self.fail:
            raise self.fail
        return [dict(i) for i in self.items]


class FakeMethodologies:
    """`MethodologiesClient` doble: cuenta las lecturas de `/career/operational-methodologies`."""

    def __init__(self, items=None, fail=None):
        self.items = METHODOLOGIES if items is None else items
        self.fail = fail
        self.list_calls = 0

    async def list(self, **kw):
        self.list_calls += 1
        if self.fail:
            raise self.fail
        return [dict(i) for i in self.items]


class Repos:
    """Estado de los repos simulados (overrides de delegación y tools, memoria)."""

    def __init__(self):
        self.delegation_overrides: dict = {}
        self.tool_overrides: dict = {}
        self.notes = list(MEMORY_NOTES)
        self.notes_fail: Optional[Exception] = None
        self.notes_calls: List[tuple] = []


@pytest.fixture
def loop():
    """Import perezoso: la colección no depende de que `services.agent_loop` exponga la interfaz nueva."""
    return importlib.import_module("services.agent_loop")


@pytest.fixture
def repos(monkeypatch):
    from repositories import profile_repo, settings_repo
    from services import memory_service

    r = Repos()

    async def list_delegation_overrides(db):
        return dict(r.delegation_overrides)

    async def get_tool_override(db, profile_id):
        return r.tool_overrides.get(profile_id)

    async def none(*a, **kw):
        return None

    async def list_agent_notes(db, user_id, profile_id, limit=40):
        r.notes_calls.append((user_id, profile_id))
        if r.notes_fail:
            raise r.notes_fail
        return list(r.notes)

    monkeypatch.setattr(profile_repo, "list_delegation_overrides", list_delegation_overrides)
    monkeypatch.setattr(profile_repo, "get_tool_override", get_tool_override)
    monkeypatch.setattr(profile_repo, "get_prompt_suffix", none)
    monkeypatch.setattr(settings_repo, "get_system_prompt_override", none)
    monkeypatch.setattr(settings_repo, "get_global_rules_override", none)
    monkeypatch.setattr(memory_service, "list_agent_notes", list_agent_notes)
    return r


def warnings_of(caplog):
    return [r for r in caplog.records if r.levelno >= logging.WARNING]


async def resolve(loop, profile_id, *, sections="default", methodologies="default", req=None):
    sections = FakeSections() if sections == "default" else sections
    methodologies = FakeMethodologies() if methodologies == "default" else methodologies
    req = req or loop.ChatTurnRequest(session_id="s1", message="hola", chat_surface="contextual")
    kw = {"sections": sections}
    if methodologies is not None:
        kw["methodologies"] = methodologies
    ctx = await loop.resolve_turn_context(object(), "u1", agent_profiles.get_profile(profile_id), req, **kw)
    return ctx, sections, methodologies


def lines_of(prompt: str) -> List[str]:
    return prompt.split("\n")


# ---------------------------------------------------------------------------------------------
# Metodologías asignadas en el prompt (api prompt.py:253-261 + methodology_scope.list_assigned_methodologies)
# ---------------------------------------------------------------------------------------------
async def test_l1_prompt_lists_assigned_and_shared_methodologies_only(loop, repos):
    ctx, sections, methodologies = await resolve(loop, ORCH)
    lines = lines_of(ctx.system_prompt)
    assert "Metodologías vigentes que te corresponden (catálogo actualizado cada turno):" in lines
    assert "- met-1: Zeta compartida (compartida)" in lines          # compartida: sin agentes ni secciones
    assert "- met-2: Alfa del orquestador" in lines                  # asignada por agent_profile_ids
    for foreign in ("Gamma ajena", "Epsilon de Networking", "Beta de Competencias", "Theta del bitácora"):
        assert foreign not in ctx.system_prompt
    assert methodologies.list_calls == 1
    assert "En este momento no hay metodologías listadas para ti." not in ctx.system_prompt


async def test_l1_methodologies_are_listed_in_title_order(loop, repos):
    ctx, *_ = await resolve(loop, ORCH)
    assert ctx.system_prompt.index("met-2: Alfa del orquestador") < ctx.system_prompt.index("met-1: Zeta compartida")


async def test_l2_prompt_groups_methodologies_by_section_with_labels(loop, repos):
    ctx, sections, methodologies = await resolve(loop, L2_IDENTITY)
    assert ctx.caller_section_ids == ["sec-1", "sec-2"]
    lines = lines_of(ctx.system_prompt)
    i1 = lines.index("  Sección sec-1 · Competencias:")
    i2 = lines.index("  Sección sec-2 · Catálogo:")
    shared = lines.index("  Compartidas (todas las secciones):")
    assert i1 < i2 < shared
    sec1 = lines[i1 + 1:i2]
    sec2 = lines[i2 + 1:shared]
    assert sec1 == ["    - met-3: Beta de Competencias", "    - met-5: Delta de Catálogo y Competencias"]
    assert sec2 == ["    - met-5: Delta de Catálogo y Competencias"]
    assert lines[shared + 1] == "    - met-1: Zeta compartida"
    # Ajenas a sus secciones y asignaciones por perfil de otros agentes: fuera.
    for foreign in ("Gamma ajena", "Epsilon de Networking", "Eta de Mapa", "Alfa del orquestador"):
        assert foreign not in ctx.system_prompt
    assert methodologies.list_calls == 1


async def test_l2_section_labels_come_from_the_same_listing_not_from_the_id(loop, repos):
    sections = FakeSections([dict(s, label=f"Etiqueta {s['id']}") for s in SECTIONS])
    ctx, *_ = await resolve(loop, L2_NETWORKING, sections=sections)
    assert "  Sección sec-7 · Etiqueta sec-7:" in ctx.system_prompt
    assert "  Sección sec-8 · Etiqueta sec-8:" in ctx.system_prompt
    assert "· sec-7:" not in ctx.system_prompt
    assert sections.list_calls == 1


async def test_l3_prompt_lists_methodologies_assigned_to_the_profile(loop, repos):
    ctx, *_ = await resolve(loop, L3_CHANGELOG)
    assert "- met-8: Theta del bitácora" in lines_of(ctx.system_prompt)
    assert "- met-1: Zeta compartida (compartida)" in lines_of(ctx.system_prompt)
    assert "Gamma ajena" not in ctx.system_prompt


async def test_without_a_methodologies_client_the_prompt_has_no_catalog_and_nothing_is_read(loop, repos):
    ctx, *_ = await resolve(loop, ORCH, methodologies=None)
    assert "En este momento no hay metodologías listadas para ti." in ctx.system_prompt
    assert "met-1" not in ctx.system_prompt


async def test_methodologies_failure_leaves_the_turn_without_catalog_and_one_warning(loop, repos, caplog):
    with caplog.at_level(logging.WARNING):
        ctx, _, methodologies = await resolve(loop, ORCH, methodologies=FakeMethodologies(fail=ApiError(500, "boom")))
    assert "En este momento no hay metodologías listadas para ti." in ctx.system_prompt
    assert ctx.profile is None or ctx.profile.id == ORCH
    assert methodologies.list_calls == 1
    assert len(warnings_of(caplog)) == 1


# ---------------------------------------------------------------------------------------------
# Delegados por overrides
# ---------------------------------------------------------------------------------------------
async def test_delegates_follow_the_override_filtered_by_level(loop, repos):
    repos.delegation_overrides = {ORCH: [L3_CHANGELOG, L2_NETWORKING, L2_NETWORKING, "agent_inexistente", ORCH]}
    ctx, *_ = await resolve(loop, ORCH)
    assert ctx.delegate_ids == [L3_CHANGELOG, L2_NETWORKING]
    assert "- agent_changelog (L3) — " in ctx.system_prompt
    assert "- agent_networking (L2) — " in ctx.system_prompt
    assert "agent_support" not in ctx.system_prompt.split("Especialistas a los que puedes delegar:")[1]
    delegate = next(t for t in ctx.tool_specs if t.name == "delegate_to_specialist")
    assert "agent_changelog" in delegate.description and "agent_networking" in delegate.description
    assert "agent_support" not in delegate.description


async def test_delegates_default_to_the_code_targets_without_override(loop, repos):
    profile = agent_profiles.get_profile(ORCH)
    ctx, *_ = await resolve(loop, ORCH)
    assert ctx.delegate_ids == profile_catalog.default_delegation_ids(profile)
    assert len(ctx.delegate_ids) > 2


async def test_an_empty_override_means_no_delegates(loop, repos):
    repos.delegation_overrides = {ORCH: []}
    ctx, *_ = await resolve(loop, ORCH)
    assert ctx.delegate_ids == []
    assert "Este perfil no tiene especialistas configurados para delegar." in ctx.system_prompt


# ---------------------------------------------------------------------------------------------
# Notas de memoria: sólo perfiles user_facing
# ---------------------------------------------------------------------------------------------
@pytest.mark.parametrize("profile_id", [ORCH, L2_NETWORKING])
async def test_memory_notes_are_loaded_for_user_facing_profiles(loop, repos, profile_id):
    ctx, *_ = await resolve(loop, profile_id)
    assert repos.notes_calls == [("u1", profile_id)]
    assert "MEMORIA PROPIA (notas de Carlos para este perfil; consúltalas siempre):" in ctx.system_prompt
    assert "- Carlos prefiere respuestas cortas" in ctx.system_prompt
    assert "- Evita jerga" in ctx.system_prompt


async def test_memory_notes_are_not_loaded_nor_shown_for_non_user_facing_profiles(loop, repos):
    assert agent_profiles.get_profile(L3_CHANGELOG).user_facing is False
    ctx, *_ = await resolve(loop, L3_CHANGELOG)
    assert repos.notes_calls == []
    assert "MEMORIA PROPIA" not in ctx.system_prompt
    assert "Carlos prefiere respuestas cortas" not in ctx.system_prompt


async def test_an_empty_memory_shows_the_empty_note_block(loop, repos):
    repos.notes = []
    ctx, *_ = await resolve(loop, ORCH)
    assert "Ahora mismo no hay ninguna." in ctx.system_prompt


async def test_memory_failure_keeps_the_turn_without_the_block_and_one_warning(loop, repos, caplog):
    repos.notes_fail = RuntimeError("bd caída")
    with caplog.at_level(logging.WARNING):
        ctx, *_ = await resolve(loop, ORCH)
    assert "MEMORIA PROPIA" not in ctx.system_prompt
    assert len(warnings_of(caplog)) == 1


# ---------------------------------------------------------------------------------------------
# Tools efectivas (incluidas las de L2 por sus secciones)
# ---------------------------------------------------------------------------------------------
async def test_l1_effective_tools_follow_the_tool_override_plus_delegation(loop, repos):
    repos.tool_overrides = {ORCH: ["list_career_record", "get_career_record"]}
    ctx, sections, _ = await resolve(loop, ORCH)
    assert ctx.allowed_tools == {"list_career_record", "get_career_record", "delegate_to_specialist"}
    assert {t.name for t in ctx.tool_specs} == ctx.allowed_tools
    assert all(isinstance(t, ToolSpec) for t in ctx.tool_specs)
    assert ctx.caller_section_ids == []
    assert sections.list_calls == 0


async def test_l1_default_tools_without_override(loop, repos):
    ctx, *_ = await resolve(loop, ORCH)
    assert ctx.allowed_tools == tools_registry.default_tool_names(agent_profiles.get_profile(ORCH)) | {
        "delegate_to_specialist"
    }


async def test_l3_effective_tools_follow_its_override(loop, repos):
    repos.tool_overrides = {L3_CHANGELOG: ["list_recent_changes"]}
    ctx, sections, _ = await resolve(loop, L3_CHANGELOG)
    assert ctx.allowed_tools == {"list_recent_changes"}
    assert "delegate_to_specialist" not in {t.name for t in ctx.tool_specs}
    assert sections.list_calls == 0


async def test_l2_effective_tools_are_the_union_of_its_sections_tools(loop, repos):
    repos.tool_overrides = {L2_NETWORKING: ["generate_pdf"]}   # un L2 no usa el override directo
    ctx, sections, _ = await resolve(loop, L2_NETWORKING)
    expected = set(profile_catalog.TABLE_SECTION_TOOLS) | {"web_search", "delegate_to_specialist"}
    assert ctx.allowed_tools == expected
    assert {t.name for t in ctx.tool_specs} == expected
    assert ctx.caller_section_ids == ["sec-7", "sec-8"]
    assert "generate_pdf" not in ctx.allowed_tools
    assert sections.list_calls == 1


async def test_l2_without_sections_has_only_delegation(loop, repos):
    ctx, sections, _ = await resolve(loop, L2_NETWORKING, sections=FakeSections([]))
    assert ctx.allowed_tools == {"delegate_to_specialist"}
    assert ctx.caller_section_ids == []
    assert sections.list_calls == 1


# ---------------------------------------------------------------------------------------------
# D-31 / D-32 en la costura
# ---------------------------------------------------------------------------------------------
@pytest.mark.parametrize("cause,text", FAILURES)
async def test_l2_sections_failure_degrades_the_context_to_the_orchestrator_with_one_warning(
    loop, repos, caplog, cause, text
):
    repos.tool_overrides = {ORCH: ["list_career_record"]}
    sections = FakeSections(fail=cause)
    with caplog.at_level(logging.WARNING):
        ctx, _, methodologies = await resolve(loop, L2_NETWORKING, sections=sections)
    assert ctx.profile is not None and ctx.profile.id == ORCH
    assert "Tu perfil es `agent_orchestrator`." in ctx.system_prompt
    assert "agent_networking" not in ctx.system_prompt.split("Tu perfil es `agent_orchestrator`.")[0]
    assert "Tu perfil es `agent_networking`." not in ctx.system_prompt
    assert ctx.allowed_tools == {"list_career_record", "delegate_to_specialist"}
    assert ctx.caller_section_ids == []
    assert sections.list_calls == 1                      # una sola lectura, sin reintentos
    assert "- met-2: Alfa del orquestador" in lines_of(ctx.system_prompt)   # catálogo del orquestador
    assert "Sección sec-7" not in ctx.system_prompt
    warnings = warnings_of(caplog)
    assert len(warnings) == 1
    assert text in warnings[0].getMessage()


async def test_non_l2_profiles_keep_their_own_profile_in_the_context(loop, repos):
    for pid in (ORCH, L3_CHANGELOG):
        ctx, *_ = await resolve(loop, pid, sections=FakeSections(fail=ApiError(500, "boom")))
        assert (ctx.profile or agent_profiles.get_profile(pid)).id == pid
        assert f"Tu perfil es `{pid}`." in ctx.system_prompt


# ---------------------------------------------------------------------------------------------
# De extremo a extremo por `chat_stream` / `run_single_turn_sync` (resolve_turn_context REAL)
# ---------------------------------------------------------------------------------------------
class Turn:
    def __init__(self):
        self.created: List[dict] = []
        self.load_args: List[tuple] = []


@pytest.fixture
def turn(monkeypatch, loop, repos):
    import services.usage_service as usage_service
    from repositories import conversation_repo, settings_repo, usage_repo

    t = Turn()

    async def get_settings(db):
        return SimpleNamespace(active_model_id=HAIKU, orchestrator_model_id=HAIKU, max_round_trips=3,
                               history_window=20, daily_budget_usd=5.0)

    async def noop(*a, **kw):
        return None

    async def spend(db, user_id):
        return 0.0

    @asynccontextmanager
    async def session_factory():
        yield FakeDb()

    async def get_or_create_conversation(db, user_id, session_id, first_message, session_type="contextual",
                                         agent_profile_id=None):
        t.created.append(dict(session_type=session_type, agent_profile_id=agent_profile_id))
        return SimpleNamespace(id="conv-1")

    async def load(db, user_id, session_id, window):
        return []

    async def build_user_content_blocks(db, user_id, message, attachments):
        return [{"text": message}]

    monkeypatch.setattr(settings_repo, "get_settings", get_settings)
    monkeypatch.setattr(usage_repo, "get_daily_spend_usd", spend)
    monkeypatch.setattr(usage_repo, "add_turn_log", noop)
    monkeypatch.setattr(usage_repo, "add_round_log", noop)
    monkeypatch.setattr(usage_service, "_default_session_factory", session_factory)
    monkeypatch.setattr(conversation_repo, "get_or_create_conversation", get_or_create_conversation)
    monkeypatch.setattr(conversation_repo, "append_message", noop)
    monkeypatch.setattr(conversation_repo, "load_converse_messages", load)
    monkeypatch.setattr(loop, "build_user_content_blocks", build_user_content_blocks)
    return t


async def stream(loop, monkeypatch, *, surface="contextual", route=None, override=None, sections=None,
                 methodologies=None, **kw):
    import services.usage_service as usage_service

    provider = FakeProvider([text_reply()])
    monkeypatch.setattr(usage_service, "_provider", lambda: provider)
    executor = Recorder()
    req_kw = {}
    if route is not None:
        req_kw["page_context"] = {"route": route}
    req = loop.ChatTurnRequest(session_id="s1", message="hola", chat_surface=surface,
                               agent_profile_id=override, **req_kw)
    call = {"provider": provider, "tool_executor": executor}
    if sections is not None:
        call["sections"] = sections
    if methodologies is not None:
        call["methodologies"] = methodologies
    events = [ev async for ev in loop.chat_stream(FakeDb(), "u1", req, **call, **kw)]
    return events, provider


async def test_route_l2_turn_reads_the_sections_once_for_profile_and_tools_and_builds_the_real_context(
    loop, turn, monkeypatch
):
    sections, methodologies = FakeSections(), FakeMethodologies()
    events, provider = await stream(loop, monkeypatch, route="/networking/map", sections=sections,
                                    methodologies=methodologies)
    assert events[-1]["type"] == "done"
    assert sections.list_calls == 1                      # D-32: perfil por ruta + tools de L2, una lectura
    assert methodologies.list_calls == 1
    request = provider.requests[0]
    assert "Tu perfil es `agent_networking`." in request.system_prompt
    assert "  Sección sec-7 · Networking:" in request.system_prompt
    assert "    - met-6: Epsilon de Networking" in request.system_prompt
    assert "  Sección sec-8 · Mapa de red:" in request.system_prompt
    assert "MEMORIA PROPIA" in request.system_prompt
    assert {t.name for t in request.tools} == set(profile_catalog.TABLE_SECTION_TOOLS) | {
        "web_search", "delegate_to_specialist"}
    assert turn.created[0]["agent_profile_id"] == "agent_networking"


async def test_explicit_l2_override_reads_the_sections_once_for_its_tools(loop, turn, monkeypatch):
    sections, methodologies = FakeSections(), FakeMethodologies()
    events, provider = await stream(loop, monkeypatch, override=L2_IDENTITY, sections=sections,
                                    methodologies=methodologies)
    assert events[-1]["type"] == "done"
    assert sections.list_calls == 1
    request = provider.requests[0]
    assert "  Sección sec-1 · Competencias:" in request.system_prompt
    assert "generate_image" in {t.name for t in request.tools}


async def test_route_l2_and_explicit_override_each_cost_at_most_one_read(loop, turn, monkeypatch):
    for kw in ({"route": "/networking"}, {"override": L2_NETWORKING, "route": "/networking"}):
        sections = FakeSections()
        await stream(loop, monkeypatch, sections=sections, methodologies=FakeMethodologies(), **kw)
        assert sections.list_calls <= 1, kw


async def test_general_surface_does_not_read_the_sections(loop, turn, monkeypatch):
    sections, methodologies = FakeSections(), FakeMethodologies()
    events, provider = await stream(loop, monkeypatch, surface="general", route="/networking",
                                    sections=sections, methodologies=methodologies)
    assert events[-1]["type"] == "done"
    assert sections.list_calls == 0
    assert methodologies.list_calls == 1
    assert "Tu perfil es `agent_orchestrator`." in provider.requests[0].system_prompt
    assert "- met-2: Alfa del orquestador" in provider.requests[0].system_prompt


@pytest.mark.parametrize("override,record_history", [(ORCH, True), (L3_CHANGELOG, False)])
async def test_non_l2_override_does_not_read_the_sections(loop, turn, monkeypatch, override, record_history):
    sections = FakeSections()
    events, provider = await stream(loop, monkeypatch, override=override, route="/networking", sections=sections,
                                    methodologies=FakeMethodologies(), record_history=record_history)
    assert events[-1]["type"] == "done"
    assert sections.list_calls == 0
    assert f"Tu perfil es `{override}`." in provider.requests[0].system_prompt


@pytest.mark.parametrize("cause,text", FAILURES)
@pytest.mark.parametrize("how", [{"route": "/networking"}, {"override": L2_NETWORKING},
                                 {"override": L2_NETWORKING, "route": "/networking"}])
async def test_failed_required_read_degrades_the_whole_turn_to_the_orchestrator_with_one_warning(
    loop, turn, monkeypatch, caplog, cause, text, how
):
    sections = FakeSections(fail=cause)
    with caplog.at_level(logging.WARNING):
        events, provider = await stream(loop, monkeypatch, sections=sections, methodologies=FakeMethodologies(),
                                        **how)
    assert events[-1]["type"] == "done"
    assert sections.list_calls == 1
    warnings = warnings_of(caplog)
    assert len(warnings) == 1
    assert text in warnings[0].getMessage()
    request = provider.requests[0]
    assert "Tu perfil es `agent_orchestrator`." in request.system_prompt
    assert "Tu perfil es `agent_networking`." not in request.system_prompt
    assert "Sección sec-7" not in request.system_prompt
    assert "web_search" not in {t.name for t in request.tools}
    assert turn.created[0]["agent_profile_id"] == ORCH


async def test_chat_stream_hands_the_methodologies_client_to_the_resolver(loop, turn, monkeypatch):
    seen = {}
    real = loop.resolve_turn_context

    async def spy(db, user_id, profile, req, *, sections, methodologies=None):
        seen["methodologies"] = methodologies
        seen["sections"] = sections
        return await real(db, user_id, profile, req, sections=sections, methodologies=methodologies)

    monkeypatch.setattr(loop, "resolve_turn_context", spy)
    methodologies, sections = FakeMethodologies(), FakeSections()
    events, _ = await stream(loop, monkeypatch, surface="general", sections=sections, methodologies=methodologies)
    assert events[-1]["type"] == "done"
    assert seen["methodologies"] is methodologies


async def test_chat_stream_without_methodologies_keeps_the_t084_resolver_signature(loop, turn, monkeypatch):
    calls = []

    async def strict(db, user_id, profile, req, *, sections):     # firma de los dobles de T-084
        calls.append(sections)
        return loop.TurnContext(system_prompt="SYS", tool_specs=[], allowed_tools=set(), caller_section_ids=[],
                                delegate_ids=[])

    monkeypatch.setattr(loop, "resolve_turn_context", strict)
    sections = FakeSections()
    events, provider = await stream(loop, monkeypatch, surface="general", sections=sections)
    assert events[-1]["type"] == "done"
    assert calls == [sections]
    assert provider.requests[0].system_prompt == "SYS"


async def test_run_single_turn_sync_forwards_the_methodologies_client(loop, turn, monkeypatch):
    import services.usage_service as usage_service

    provider = FakeProvider([text_reply("listo")])
    monkeypatch.setattr(usage_service, "_provider", lambda: provider)
    sections, methodologies = FakeSections(), FakeMethodologies()
    done = await loop.run_single_turn_sync(
        FakeDb(), user_id="u1", session_id="s1", message="hola", provider=provider, tool_executor=Recorder(),
        sections=sections, methodologies=methodologies, chat_surface="general",
    )
    assert done["type"] == "done"
    assert methodologies.list_calls == 1
    assert "- met-2: Alfa del orquestador" in provider.requests[0].system_prompt
    assert sections.list_calls == 0
