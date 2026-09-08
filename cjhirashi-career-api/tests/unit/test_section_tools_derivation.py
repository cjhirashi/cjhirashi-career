"""Herramientas de una sección, derivadas en código (spec 004, RF-001).

- `search_knowledge_base` SIEMPRE (baseline de consulta).
- Sección tabla -> + el CRUD genérico de su `resource_key`.
- Sección funcional operativa -> + sus `related_tools` (meta-tools).
- Sección de monitoreo (métricas, visor) -> sólo el baseline (correcto).
"""
import pytest

from services.admin_sections import get_section_spec, list_section_specs, tools_for_section

_TABLE_CRUD = {
    "list_career_record",
    "get_career_record",
    "create_career_record",
    "update_career_record",
    "delete_career_record",
    "bulk_update_career_record",
    "count_career_records",
    "describe_resource_schema",
    "search_knowledge_base",
}


@pytest.mark.requisito("RF-001")
def test_table_section_derives_full_crud_set():
    # sec-32 = career "projects" (tabla)
    spec = get_section_spec("sec-32")
    assert spec.section_type == "table" and spec.resource_key == "projects"
    tools = tools_for_section(spec)
    assert _TABLE_CRUD <= tools
    assert "get_linkedin_status" not in tools
    assert "pdf_template" not in tools


@pytest.mark.requisito("RF-001")
def test_functional_section_is_baseline_plus_related_tools():
    # sec-6 = LinkedIn · Publicar (funcional operativa)
    spec = get_section_spec("sec-6")
    assert spec.section_type == "functional"
    tools = tools_for_section(spec)
    assert tools == {"search_knowledge_base"} | set(spec.related_tools)
    assert "get_linkedin_status" in tools
    assert "list_career_record" not in tools


@pytest.mark.requisito("RF-001")
def test_search_knowledge_base_is_the_universal_baseline():
    """Toda sección puede consultar su base de conocimiento — ninguna queda sin tools."""
    toolless = [s.id for s in list_section_specs() if not tools_for_section(s)]
    assert toolless == []
    for s in list_section_specs():
        assert "search_knowledge_base" in tools_for_section(s), s.id


@pytest.mark.requisito("RF-001")
def test_operative_config_sections_have_their_meta_tool():
    assert "agent_catalog_settings" in tools_for_section(get_section_spec("sec-16"))  # catálogo de agentes
    assert "admin_section_settings" in tools_for_section(get_section_spec("sec-17"))  # secciones del Admin
    assert "bedrock_global_settings" in tools_for_section(get_section_spec("sec-18"))  # prompts globales
    assert "bedrock_global_settings" in tools_for_section(get_section_spec("sec-13"))  # instrucciones
    assert "error_report_settings" in tools_for_section(get_section_spec("sec-19"))  # reportes de falla


@pytest.mark.requisito("RF-001")
def test_monitoring_sections_have_only_the_baseline():
    # métricas: monitoreo, sin operación → sólo consulta
    for sid in ("sec-1", "sec-2", "sec-3", "sec-4"):
        assert tools_for_section(get_section_spec(sid)) == {"search_knowledge_base"}
