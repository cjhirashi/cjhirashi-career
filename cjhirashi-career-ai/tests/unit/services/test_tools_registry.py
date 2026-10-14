"""RF-001 / RF-003: catálogo de tools del harness (esquemas; la ejecución es del Bloque F) (T-070)."""
import pytest

from providers.base import ToolSpec
from services import agent_profiles as ap

pytestmark = pytest.mark.requisito("RF-001")


def test_search_knowledge_base_retirada_d15():
    from services import tools_registry as tr

    assert "search_knowledge_base" not in tr.all_tool_names()
    blob = " ".join(t["description"] for t in tr._RAW_TOOLS)
    assert "search_knowledge_base" not in blob and "Qdrant" not in blob


def test_catalogo_incluye_el_crud_generico_y_la_delegacion():
    from services import tools_registry as tr

    assert {
        "list_career_record", "get_career_record", "create_career_record", "update_career_record",
        "delete_career_record", "bulk_update_career_record", "count_career_records",
        "describe_resource_schema", "delegate_to_specialist",
    } <= tr.all_tool_names()


def test_cada_tool_nombrada_por_un_perfil_existe_en_el_catalogo():
    from services import tools_registry as tr

    missing = {
        (p.id, n)
        for p in ap.list_profiles()
        for n in (p.allowed_tool_names or set())
        if n not in tr.all_tool_names()
    }
    assert missing == set()


def test_tool_scope():
    from services import tools_registry as tr

    assert tr.tool_scope("list_career_record") == "section"
    assert tr.tool_scope("delegate_to_specialist") == "agent"
    assert tr.tool_scope("generate_pdf") == "both"
    assert tr.tool_scope("no_existe") == "both"


def test_write_tools_son_un_subconjunto_del_catalogo():
    from services import tools_registry as tr

    assert tr.WRITE_TOOLS <= tr.all_tool_names()
    assert "create_career_record" in tr.WRITE_TOOLS and "list_career_record" not in tr.WRITE_TOOLS


def test_tool_specs_filtra_por_allowed_y_devuelve_toolspec():
    from services import tools_registry as tr

    specs = tr.tool_specs({"list_career_record", "get_career_record"})
    assert {s.name for s in specs} == {"list_career_record", "get_career_record"}
    assert all(isinstance(s, ToolSpec) and isinstance(s.input_schema, dict) for s in specs)
    assert len(tr.tool_specs(None)) == len(tr.all_tool_names())


def test_tool_specs_describe_destinos_de_delegacion_del_caller():
    from services import tools_registry as tr

    caller = ap.get_profile("agent_orchestrator")
    [spec] = tr.tool_specs({"delegate_to_specialist"}, caller_profile=caller, delegate_ids=["agent_support"])
    assert "agent_support" in spec.description
    assert "agent_networking" not in spec.description


def test_catalogo_integrado_expone_nombre_descripcion_y_scope():
    from services import tools_registry as tr

    cat = tr.list_builtin_tool_catalog()
    assert {c["name"] for c in cat} == tr.all_tool_names()
    row = next(c for c in cat if c["name"] == "count_career_records")
    assert row["scope"] == "section" and row["description"]


def test_default_tool_names_por_nivel():
    from services import tools_registry as tr

    assert tr.default_tool_names(ap.get_profile("agent_orchestrator")) == {"delegate_to_specialist"}
    l3 = ap.get_profile("agent_changelog")
    assert "delegate_to_specialist" not in tr.default_tool_names(l3)


def test_effective_l2_usa_las_tools_de_seccion_y_agrega_delegacion():
    from services import tools_registry as tr

    l2 = ap.get_profile("agent_professional_identity")
    eff = tr.effective_tool_names(l2, None, section_tools={"list_career_record", "inexistente"})
    assert eff == {"list_career_record", "delegate_to_specialist"}


def test_effective_override_reemplaza_en_l3_y_l3_nunca_delega():
    from services import tools_registry as tr

    l3 = ap.get_profile("agent_changelog")
    eff = tr.effective_tool_names(l3, ["list_recent_changes", "delegate_to_specialist", "inexistente"])
    assert eff == {"list_recent_changes"}


def test_validate_normaliza_y_rechaza_desconocidas_y_de_seccion():
    from services import tools_registry as tr

    assert tr.validate_tool_names(["generate_pdf", "generate_pdf", "list_recent_changes"]) == [
        "generate_pdf", "list_recent_changes",
    ]
    with pytest.raises(ValueError, match="Unknown tool names"):
        tr.validate_tool_names(["nope"])
    with pytest.raises(ValueError, match="sección"):
        tr.validate_tool_names(["list_career_record"])
