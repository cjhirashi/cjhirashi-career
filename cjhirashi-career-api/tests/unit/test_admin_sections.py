"""Registro de secciones Admin y matching de rutas."""
import re

import pytest

from services.admin_sections import (
    SECTION_BUCKET,
    SECTION_FUNCTIONAL,
    SECTION_METRICS,
    SECTION_TABLE,
    get_section_by_system_name,
    get_section_spec,
    is_l2,
    list_section_specs,
    match_section,
)
from services.section_catalog import _serialize
from services.bedrock.agent_profiles import (
    AGENT_CONFIGURATION,
    AGENT_DIGITAL_PRESENCE,
    AGENT_ORCHESTRATOR,
    AGENT_PDF_DESIGN,
    AGENT_SEARCH_OPERATIONS,
    get_profile,
)

_SEC_RE = re.compile(r"^sec-[1-9]\d*$")


def test_linkedin_is_functional_owned_by_digital_presence():
    spec = get_section_by_system_name("linkedin-publish")
    assert spec.section_type == SECTION_FUNCTIONAL
    # feature 001: el L3 agent_linkedin_publishing ya no es dueño de sección;
    # el chat contextual de LinkedIn lo atiende el L2 de Presencia Digital.
    assert spec.default_agent_profile_id == AGENT_DIGITAL_PRESENCE
    assert "get_linkedin_status" in spec.related_tools


def test_job_discovery_is_functional():
    spec = get_section_by_system_name("job-discovery")
    assert spec.section_type == SECTION_FUNCTIONAL
    assert spec.default_agent_profile_id == AGENT_SEARCH_OPERATIONS


def test_defaults_are_l2_or_none():
    """RF-004: toda default_agent_profile_id es un agente L2 o None (nunca L1/L3)."""
    for spec in list_section_specs():
        pid = spec.default_agent_profile_id
        if pid is None:
            continue
        assert get_profile(pid).level == 2, f"{spec.id} apunta a {pid} (no L2)"


def test_l1_l3_sections_remapped():
    """RF-004: re-mapeo de las 11 secciones que apuntaban a L1/L3."""
    by_id = {s.id: s.default_agent_profile_id for s in list_section_specs()}
    assert by_id["sec-1"] is None
    assert by_id["sec-2"] is None
    assert by_id["sec-4"] is None
    assert by_id["sec-5"] is None
    assert by_id["sec-10"] is None
    assert by_id["sec-11"] is None
    assert by_id["sec-6"] == AGENT_DIGITAL_PRESENCE
    assert by_id["sec-7"] == AGENT_SEARCH_OPERATIONS
    assert by_id["sec-12"] == AGENT_CONFIGURATION
    assert by_id["sec-13"] == AGENT_CONFIGURATION
    assert by_id["sec-14"] == AGENT_CONFIGURATION


def test_is_l2_helper():
    assert is_l2(AGENT_CONFIGURATION) is True
    assert is_l2(AGENT_ORCHESTRATOR) is False  # L1
    assert is_l2("agent_task_manager") is False  # L3
    assert is_l2("does-not-exist") is False


def test_files_is_bucket_and_dashboard_is_metrics():
    types = {s.system_name: s.section_type for s in list_section_specs()}
    assert types["files"] == SECTION_BUCKET
    assert types["dashboard"] == SECTION_METRICS
    assert types["career-vacancies"] == SECTION_TABLE


def test_match_career_record_view():
    matched = match_section("/career/vacancies/vac-1")
    assert matched is not None
    spec, view_key = matched
    assert spec.system_name == "career-vacancies"
    assert view_key == "view"


def test_match_settings_agents():
    matched = match_section("/settings/agents/agent_pdf_design")
    assert matched is not None
    spec, view_key = matched
    assert spec.system_name == "settings-agents"
    assert spec.section_type == SECTION_TABLE
    assert view_key == "view"
    assert {v.key for v in spec.views} == {"list", "view", "edit"}
    list_body = next(v.sidebar_body for v in spec.views if v.key == "list")
    assert "no se pueden crear" in list_body.lower()


def test_pdf_sections_belong_to_design_agent():
    owned = [
        s.system_name
        for s in list_section_specs()
        if s.default_agent_profile_id == AGENT_PDF_DESIGN
    ]
    assert "pdf-templates" in owned
    assert "pdf-styles" in owned


def test_every_section_serializes_without_override():
    specs = list_section_specs()
    assert len(specs) >= 40
    for spec in specs:
        item = _serialize(spec, None)
        assert item["id"] == spec.id
        assert item["system_name"] == spec.system_name
        assert item["view_count"] == len(spec.views)
        assert item["section_type"] == spec.section_type


def test_tasks_is_top_level_with_board_views():
    spec = get_section_by_system_name("agent-tasks")
    assert spec.path == "/tasks"
    assert spec.group == "Principal"
    assert {v.key for v in spec.views} >= {"list", "calendar", "kanban", "gantt", "view", "edit"}
    matched = match_section("/tasks")
    assert matched is not None
    assert matched[0].system_name == "agent-tasks"


def test_ids_are_synthetic_and_unique():
    specs = list_section_specs()
    ids = [s.id for s in specs]
    system_names = [s.system_name for s in specs]
    assert len(ids) == len(set(ids)), "PK sec-N duplicado"
    assert len(system_names) == len(set(system_names)), "system_name duplicado"
    for spec in specs:
        assert _SEC_RE.match(spec.id), f"{spec.id!r} no tiene formato sec-N"


# Mapa CONGELADO completo sec-N <-> system_name (ADR-021). Debe cuadrar 1:1 con
# _SECTIONS + _CAREER_ROWS y con _SLUG_TO_PK de la migración b2c3d4e5f6a7.
_FROZEN_MAP = {
    "sec-1": "dashboard",
    "sec-2": "metrics",
    "sec-3": "search-metrics",
    "sec-4": "agent-metrics",
    "sec-5": "files",
    "sec-6": "linkedin-publish",
    "sec-7": "job-discovery",
    "sec-8": "pdf-templates",
    "sec-9": "pdf-styles",
    "sec-10": "agent-tasks",
    "sec-11": "agent-chat",
    "sec-12": "agent-memory",
    "sec-13": "agent-instructions",
    "sec-14": "agent-tools",
    "sec-15": "agent-audit-log",
    "sec-16": "settings-agents",
    "sec-17": "settings-sections",
    "sec-18": "settings-agent-prompts",
    "sec-19": "settings-error-reports",
    "sec-20": "career-personal-profile",
    "sec-21": "career-differentiators",
    "sec-22": "career-identity",
    "sec-23": "career-identity-reflections",
    "sec-24": "career-competencies",
    "sec-25": "career-certifications",
    "sec-26": "career-target-roles",
    "sec-27": "career-work-history",
    "sec-28": "career-achievements",
    "sec-29": "career-star-stories",
    "sec-30": "career-career-reviews",
    "sec-31": "career-role-gap-analysis",
    "sec-32": "career-projects",
    "sec-33": "career-fit-scoring-factors",
    "sec-34": "career-market-segments",
    "sec-35": "career-role-narratives",
    "sec-36": "career-search-plans",
    "sec-37": "career-networking-contacts",
    "sec-38": "career-target-companies",
    "sec-39": "career-vacancies",
    "sec-40": "career-cv-versions",
    "sec-41": "career-cover-letter-versions",
    "sec-42": "career-applications",
    "sec-43": "career-application-interactions",
    "sec-44": "career-interviews",
    "sec-45": "career-linkedin-profile",
    "sec-46": "career-github-profile",
    "sec-47": "career-portal-home",
    "sec-48": "career-portal-about",
    "sec-49": "career-portal-contact",
    "sec-50": "career-publications",
    "sec-51": "career-contact-interactions",
    "sec-52": "career-networking-activities",
    "sec-53": "career-tags",
    "sec-54": "career-operational-methodologies",
}


def test_frozen_numbering_full_map():
    """El mapa completo sec-N <-> system_name (1..54) está congelado (ADR-021)."""
    live = {spec.id: spec.system_name for spec in list_section_specs()}
    assert live == _FROZEN_MAP
    # Fronteras y ancla explícitas.
    assert get_section_spec("sec-19").system_name == "settings-error-reports"
    assert get_section_spec("sec-20").system_name == "career-personal-profile"
    assert get_section_spec("sec-54").system_name == "career-operational-methodologies"
    assert get_section_by_system_name("career-projects").id == "sec-32"


def test_numbering_is_monotonic_without_integer_collisions():
    nums = [int(spec.id.split("-")[1]) for spec in list_section_specs()]
    assert len(nums) == len(set(nums)), "entero sec-N repetido en el registro"
    assert min(nums) >= 1
    assert max(nums) <= 54, "sec-N por encima del high-water actual"
    # Hoy la asignación es contigua 1..54 (sin huecos todavía).
    assert sorted(nums) == list(range(1, 55))


def test_lookup_unknown_keys_raise_keyerror():
    with pytest.raises(KeyError):
        get_section_spec("dashboard")  # slug ya no es PK
    with pytest.raises(KeyError):
        get_section_spec("sec-9999")
    with pytest.raises(KeyError):
        get_section_by_system_name("sec-1")  # PK no es system_name
    with pytest.raises(KeyError):
        get_section_by_system_name("does-not-exist")


def test_career_sections_system_name_is_prefixed_resource_key():
    for spec in list_section_specs():
        if spec.resource_key and spec.path.startswith("/career/"):
            assert spec.system_name == f"career-{spec.resource_key}"
