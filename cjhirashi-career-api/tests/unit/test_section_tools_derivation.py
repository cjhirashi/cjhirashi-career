"""Herramientas de una sección, derivadas en código (spec 004, RF-001).

Una sección tabla -> el set CRUD de su `resource_key` + búsqueda de conocimiento.
Una sección funcional/métricas/bucket -> exactamente sus `related_tools`.
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
    # no arrastra herramientas de otra sección
    assert "get_linkedin_status" not in tools
    assert "pdf_template" not in tools


@pytest.mark.requisito("RF-001")
def test_functional_section_is_exactly_related_tools():
    # sec-6 = LinkedIn · Publicar (funcional)
    spec = get_section_spec("sec-6")
    assert spec.section_type == "functional"
    tools = tools_for_section(spec)
    assert tools == set(spec.related_tools)
    assert "get_linkedin_status" in tools
    assert "list_career_record" not in tools


@pytest.mark.requisito("RF-001")
def test_derivation_is_pure_and_total():
    # toda sección resuelve a un set (posiblemente vacío), sin excepción
    for spec in list_section_specs():
        result = tools_for_section(spec)
        assert isinstance(result, set)
        if spec.section_type == "table" and spec.resource_key:
            assert "search_knowledge_base" in result
