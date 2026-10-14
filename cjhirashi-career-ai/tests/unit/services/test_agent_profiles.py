"""RF-012: perfiles de agente trasladados de la API (sin search_knowledge_base, D-15) (T-068)."""
import pytest

pytestmark = pytest.mark.requisito("RF-012")


def test_search_knowledge_base_no_aparece_en_ningun_perfil():
    from services import agent_profiles

    for p in agent_profiles.list_profiles():
        assert "search_knowledge_base" not in (p.allowed_tool_names or set()), p.id
        assert "search_knowledge_base" not in p.system_prompt_suffix, p.id
    assert "search_knowledge_base" not in agent_profiles._L2_BASE_TOOL_NAMES


def test_get_profile_acepta_nombre_de_sistema_y_record_id():
    from services import agent_profiles as ap

    assert ap.get_profile("agent_orchestrator").level == 1
    assert ap.get_profile("agent-1").id == "agent_orchestrator"
    assert ap.agent_record_id("agent_configuration") == "agent-20"
    assert ap.canonical_profile_id("agent-7") == "agent_methodologies"
    with pytest.raises(KeyError):
        ap.get_profile("agent_nope")
    with pytest.raises(KeyError):
        ap.agent_record_id("agent_nope")


def test_niveles_y_user_facing():
    from services import agent_profiles as ap

    niveles = {p.level for p in ap.list_profiles()}
    assert niveles == {1, 2, 3}
    assert {p.id for p in ap.list_user_facing_profiles()} == {p.id for p in ap.list_profiles() if p.level in (1, 2)}
    assert ap.get_profile(ap.AGENT_ORCHESTRATOR).can_delegate
    assert not ap.get_profile(ap.AGENT_GITHUB).can_delegate


def test_delegacion_solo_hacia_abajo():
    from services import agent_profiles as ap

    l1, l2, l3 = (ap.get_profile(x) for x in (ap.AGENT_ORCHESTRATOR, ap.AGENT_SUPPORT, ap.AGENT_GITHUB))
    assert ap.can_delegate_to(l1, l2) and ap.can_delegate_to(l1, l3)
    assert ap.can_delegate_to(l2, l3)
    assert not ap.can_delegate_to(l2, l1) and not ap.can_delegate_to(l2, l2)
    assert not ap.can_delegate_to(l3, l3)
    assert all(t.level == 3 for t in ap.delegation_targets(l2))
    assert ap.delegation_targets(l3) == []


def test_delegation_error_mensajes():
    from services import agent_profiles as ap

    l2 = ap.get_profile(ap.AGENT_SUPPORT)
    assert ap.delegation_error(l2, ap.AGENT_GITHUB) is None
    assert "unknown agent profile" in ap.delegation_error(l2, "agent_nope")
    assert "not allowed" in ap.delegation_error(l2, ap.AGENT_ORCHESTRATOR)
    assert "configured targets" in ap.delegation_error(l2, ap.AGENT_GITHUB, allowed_ids={ap.AGENT_WEB_SEARCH})
    assert ap.delegation_error(l2, ap.AGENT_GITHUB, allowed_ids={ap.AGENT_GITHUB}) is None


def test_descripcion_de_la_tool_de_delegacion():
    from services import agent_profiles as ap

    l2 = ap.get_profile(ap.AGENT_SUPPORT)
    todo = ap.delegate_tool_description(l2)
    assert "agent_github" in todo and "L3" in todo
    solo = ap.delegate_tool_description(l2, target_ids=["agent_github", "agent_nope"])
    assert "agent_github" in solo and "agent_web_search" not in solo
    assert "no está disponible" in ap.delegate_tool_description(ap.get_profile(ap.AGENT_GITHUB))
    assert "no está disponible" in ap.delegate_tool_description(l2, target_ids=[])


def test_resolve_agent_profile_enruta_por_superficie_ruta_y_recurso():
    from services import agent_profiles as ap

    r = ap.resolve_agent_profile
    assert r(chat_surface="general", agent_profile_id="agent_support", page_context=None).id == ap.AGENT_ORCHESTRATOR
    assert r(chat_surface="contextual", agent_profile_id="agent_support", page_context=None).id == ap.AGENT_SUPPORT
    assert r(chat_surface="contextual", agent_profile_id=None, page_context={"route": "/linkedin"}).id == ap.AGENT_DIGITAL_PRESENCE
    assert r(chat_surface="contextual", agent_profile_id=None,
             page_context={"route": "/job-discovery/preview"}).id == ap.AGENT_SEARCH_OPERATIONS
    assert r(chat_surface="contextual", agent_profile_id=None,
             page_context={"route": "/x", "resource_key": "tags"}).id == ap.AGENT_SUPPORT
    assert r(chat_surface="contextual", agent_profile_id=None, page_context={"route": "/x"}).id == ap.AGENT_ORCHESTRATOR
    assert r(chat_surface="contextual", agent_profile_id=None, page_context=None).id == ap.AGENT_ORCHESTRATOR


def test_tools_for_profile_aplica_nivel_y_catalogo():
    from services import agent_profiles as ap

    todas = {"delegate_to_specialist", "list_career_record", "get_career_record", "create_career_record",
             "describe_resource_schema", "count_career_records", "update_career_record",
             "bulk_update_career_record", "delete_career_record", "generate_pdf", "get_github_repo"}
    assert ap.tools_for_profile(ap.get_profile(ap.AGENT_ORCHESTRATOR), todas) == {"delegate_to_specialist"}
    l2 = ap.tools_for_profile(ap.get_profile(ap.AGENT_SUPPORT), todas)
    assert "delegate_to_specialist" in l2 and "list_career_record" in l2
    l3 = ap.tools_for_profile(ap.get_profile(ap.AGENT_PDF_RENDER), todas)
    assert l3 == {"generate_pdf"}


def test_perfil_puede_leer_metodologias_sin_search_knowledge_base():
    from services import agent_profiles as ap

    assert ap.profile_can_read_methodologies(ap.get_profile(ap.AGENT_SUPPORT)) is True
    assert ap.profile_can_read_methodologies(ap.get_profile(ap.AGENT_ORCHESTRATOR)) is False
    assert ap.profile_can_read_methodologies(ap.get_profile(ap.AGENT_CV_WRITING)) is True
    assert ap.profile_can_read_methodologies(ap.get_profile(ap.AGENT_GITHUB)) is False
    assert not hasattr(ap, "profile_can_search_knowledge")


# D-28: paridad exacta con `profile_can_search_knowledge` de la API. Lista copiada (NO se
# importa en runtime) de `cjhirashi-career-api/src/services/bedrock/agent_profiles.py`:
#   - L2 sin allowed_tool_names (usan _L2_BASE_TOOL_NAMES, l.96-106): lineas 440-548
#     (professional_identity, search_operations, digital_presence, networking, support,
#     methodologies) y la regla `level == 2` de `profile_can_search_knowledge` (l.919-923);
#   - perfiles con `search_knowledge_base` en su conjunto: _PDF_DESIGN_TOOL_NAMES (l.122-123,
#     agent_pdf_design), _VISUAL_TOOL_NAMES (l.140, agent_visual_design),
#     _DOCUMENT_WRITING_TOOL_NAMES (l.167, agent_cv_writing y agent_cover_letter_writing),
#     _CONFIGURATION_TOOL_NAMES (l.194, agent_configuration), _SETTINGS_TOOL_NAMES (l.201,
#     agent_settings).
# agent_task_manager (l.145-154) NO tiene search_knowledge_base aunque si get_career_record.
_API_PUEDEN_BUSCAR_KB = {
    "agent_professional_identity",
    "agent_search_operations",
    "agent_digital_presence",
    "agent_networking",
    "agent_support",
    "agent_methodologies",
    "agent_pdf_design",
    "agent_visual_design",
    "agent_cv_writing",
    "agent_cover_letter_writing",
    "agent_settings",
    "agent_configuration",
}


def test_d28_lectura_de_metodologias_identica_a_la_api_en_los_20_perfiles():
    from services import agent_profiles as ap

    perfiles = ap.list_profiles()
    assert len(perfiles) == 20
    lectores = {p.id for p in perfiles if ap.profile_can_read_methodologies(p)}
    assert lectores == _API_PUEDEN_BUSCAR_KB


@pytest.mark.parametrize(
    "pid", ["agent_pdf_design", "agent_settings", "agent_configuration", "agent_visual_design"]
)
def test_d28_cuatro_perfiles_ganan_lectura_con_tools_de_carrera(pid):
    from services import agent_profiles as ap

    p = ap.get_profile(pid)
    assert ap.profile_can_read_methodologies(p) is True
    assert {"list_career_record", "get_career_record"} <= p.allowed_tool_names


def test_d28_task_manager_no_gana_lectura_de_metodologias():
    from services import agent_profiles as ap

    p = ap.get_profile("agent_task_manager")
    assert ap.profile_can_read_methodologies(p) is False
    assert "get_career_record" in p.allowed_tool_names  # sigue operando sus tablas


def test_d28_todo_lector_tiene_las_tools_de_lectura_en_su_conjunto_efectivo():
    from services import agent_profiles as ap
    from services import tools_registry as tr

    for p in ap.list_profiles():
        if ap.profile_can_read_methodologies(p):
            tools = ap.tools_for_profile(p, tr.all_tool_names())
            assert {"list_career_record", "get_career_record"} <= tools, p.id
