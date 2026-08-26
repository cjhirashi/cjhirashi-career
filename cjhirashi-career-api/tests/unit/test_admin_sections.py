"""Registro de secciones Admin y matching de rutas."""
from services.admin_sections import (
    SECTION_BUCKET,
    SECTION_FUNCTIONAL,
    SECTION_METRICS,
    SECTION_TABLE,
    chat_agent_id,
    list_section_specs,
    match_section,
)
from services.section_catalog import _serialize
from services.bedrock.agent_profiles import (
    AGENT_DIGITAL_PRESENCE,
    AGENT_LINKEDIN_PUBLISHING,
    AGENT_PDF_DESIGN,
    AGENT_VACANCY_SEARCH,
)


def test_linkedin_is_functional_owned_by_publishing_agent():
    spec = next(s for s in list_section_specs() if s.id == "linkedin-publish")
    assert spec.section_type == SECTION_FUNCTIONAL
    assert spec.default_agent_profile_id == AGENT_LINKEDIN_PUBLISHING
    assert "get_linkedin_status" in spec.related_tools
    assert chat_agent_id(spec.default_agent_profile_id) == AGENT_DIGITAL_PRESENCE


def test_job_discovery_is_functional():
    spec = next(s for s in list_section_specs() if s.id == "job-discovery")
    assert spec.section_type == SECTION_FUNCTIONAL
    assert spec.default_agent_profile_id == AGENT_VACANCY_SEARCH


def test_files_is_bucket_and_dashboard_is_metrics():
    types = {s.id: s.section_type for s in list_section_specs()}
    assert types["files"] == SECTION_BUCKET
    assert types["dashboard"] == SECTION_METRICS
    assert types["career-vacancies"] == SECTION_TABLE


def test_match_career_record_view():
    matched = match_section("/career/vacancies/vac-1")
    assert matched is not None
    spec, view_key = matched
    assert spec.id == "career-vacancies"
    assert view_key == "view"


def test_match_settings_agents():
    matched = match_section("/settings/agents/agent_pdf_design")
    assert matched is not None
    spec, view_key = matched
    assert spec.id == "settings-agents"
    assert spec.section_type == SECTION_TABLE
    assert view_key == "view"
    assert {v.key for v in spec.views} == {"list", "view", "edit"}
    list_body = next(v.sidebar_body for v in spec.views if v.key == "list")
    assert "no se pueden crear" in list_body.lower()


def test_pdf_sections_belong_to_design_agent():
    owned = [s.id for s in list_section_specs() if s.default_agent_profile_id == AGENT_PDF_DESIGN]
    assert "pdf-templates" in owned
    assert "pdf-styles" in owned


def test_every_section_serializes_without_override():
    specs = list_section_specs()
    assert len(specs) >= 40
    for spec in specs:
        item = _serialize(spec, None)
        assert item["id"] == spec.id
        assert item["view_count"] == len(spec.views)
        assert item["section_type"] == spec.section_type



def test_tasks_is_top_level_with_board_views():
    spec = next(s for s in list_section_specs() if s.id == "agent-tasks")
    assert spec.path == "/tasks"
    assert spec.group == "Principal"
    assert {v.key for v in spec.views} >= {"list", "calendar", "kanban", "gantt", "view", "edit"}
    matched = match_section("/tasks")
    assert matched is not None
    assert matched[0].id == "agent-tasks"
