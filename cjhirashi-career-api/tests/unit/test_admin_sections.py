"""Registro en código de la jerarquía de secciones del Admin (ADR-022)."""
import re

import pytest

from services.admin_sections import (
    DATA_SOURCES,
    GROUPS,
    SECTION_BUCKET,
    SECTION_FUNCTIONAL,
    SECTION_METRICS,
    SECTION_TABLE,
    get_section_by_system_name,
    get_section_spec,
    list_section_specs,
    match_section,
)
from services.bedrock.agent_profiles import (
    AGENT_LINKEDIN_PUBLISHING,
    AGENT_PDF_DESIGN,
    AGENT_VACANCY_SEARCH,
)

_S1_RE = re.compile(r"^s1-[1-9]\d*$")


def test_registry_has_54_sections_and_11_groups():
    specs = list_section_specs()
    assert len(specs) == 54
    assert len(GROUPS) == 11
    names = {name for _gid, _sys, name, _so in GROUPS}
    assert {s.group for s in specs} <= names


def test_section_ids_are_s1_prefixed_and_unique():
    specs = list_section_specs()
    ids = [s.id for s in specs]
    assert len(ids) == len(set(ids))
    for spec in specs:
        assert _S1_RE.match(spec.id), spec.id


def test_sec_n_integer_is_preserved_1_to_54():
    live = {int(s.id.split("-")[1]): s.system_name for s in list_section_specs()}
    assert sorted(live) == list(range(1, 55))
    assert live[1] == "dashboard"
    assert live[19] == "settings-error-reports"
    assert live[20] == "career-personal-profile"
    assert live[54] == "career-operational-methodologies"


def test_section_types_and_data_source_inference():
    types = {s.system_name: s.section_type for s in list_section_specs()}
    assert types["files"] == SECTION_BUCKET
    assert types["dashboard"] == SECTION_METRICS
    assert types["linkedin-publish"] == SECTION_FUNCTIONAL
    assert types["career-vacancies"] == SECTION_TABLE

    dashboard = get_section_by_system_name("dashboard")
    assert dashboard.views[0].data_source == "computed"
    linkedin = get_section_by_system_name("linkedin-publish")
    assert linkedin.views[0].data_source == "external"
    personal = get_section_by_system_name("career-personal-profile")  # singleton
    assert personal.singleton is True
    assert [v.key for v in personal.views] == ["main"]
    assert personal.views[0].data_source == "singleton"
    assert personal.views[0].resource_key == "personal-profile"
    competencies = get_section_by_system_name("career-competencies")
    assert [v.key for v in competencies.views] == ["list", "view", "edit"]
    assert all(v.data_source == "crud" for v in competencies.views)


def test_resource_key_only_on_crud_or_singleton_views():
    for spec in list_section_specs():
        for view in spec.views:
            assert view.data_source in DATA_SOURCES
            if view.resource_key is not None:
                assert view.data_source in ("crud", "singleton")


def test_no_section_declares_more_than_10_views():
    for spec in list_section_specs():
        assert 1 <= len(spec.views) <= 10


def test_paths_unique_global():
    paths = [s.path for s in list_section_specs() if s.path]
    assert len(paths) == len(set(paths))


def test_related_tools_flow_into_views():
    linkedin = get_section_by_system_name("linkedin-publish")
    assert "get_linkedin_status" in linkedin.views[0].tool_names
    assert linkedin.default_agent_profile_id == AGENT_LINKEDIN_PUBLISHING


def test_tasks_section_has_board_views():
    spec = get_section_by_system_name("agent-tasks")
    assert spec.path == "/tasks"
    assert spec.group == "Principal"
    assert {v.key for v in spec.views} >= {"list", "calendar", "kanban", "gantt", "view", "edit"}


def test_pdf_sections_belong_to_design_agent():
    owned = {
        s.system_name
        for s in list_section_specs()
        if s.default_agent_profile_id == AGENT_PDF_DESIGN
    }
    assert {"pdf-templates", "pdf-styles"} <= owned


def test_job_discovery_owned_by_vacancy_search():
    spec = get_section_by_system_name("job-discovery")
    assert spec.section_type == SECTION_FUNCTIONAL
    assert spec.default_agent_profile_id == AGENT_VACANCY_SEARCH


def test_match_section_exact_and_detail():
    exact = match_section("/career/vacancies")
    assert exact is not None and exact[0].system_name == "career-vacancies"
    assert exact[1] == "list"
    detail = match_section("/career/vacancies/vac-1")
    assert detail is not None and detail[1] == "view"
    assert match_section("/does/not/exist") is None


def test_lookup_unknown_ids_raise_keyerror():
    with pytest.raises(KeyError):
        get_section_spec("sec-1")  # prefijo viejo ya no es PK
    with pytest.raises(KeyError):
        get_section_spec("s1-9999")
    with pytest.raises(KeyError):
        get_section_by_system_name("s1-1")
