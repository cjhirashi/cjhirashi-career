"""RF-001: composición del system prompt (default / override en BD / sufijo de perfil) (T-070)."""
import pytest

from services import agent_profiles as ap

pytestmark = pytest.mark.requisito("RF-001")


def test_reglas_globales_por_defecto_son_grounding_mas_asignacion():
    from services import prompt

    rules = prompt.default_global_rules()
    assert rules == "\n\n".join([prompt.GROUNDING_RULE, prompt._METHODOLOGY_ASSIGNMENT_RULE])
    assert "NO ALUCINAR" in rules


def test_prompt_base_lista_recursos_y_no_menciona_search_knowledge_base():
    from services import prompt

    text = prompt.default_system_prompt(["vacancies", "achievements"])
    assert "Recursos disponibles (resource_key): achievements, vacancies." in text
    assert "search_knowledge_base" not in text
    assert "operational-methodologies" in text


def test_prompt_base_sin_lista_usa_los_recursos_de_los_perfiles():
    from services import prompt

    text = prompt.default_system_prompt()
    assert "Recursos disponibles (resource_key):" in text and "vacancies" in text


def test_bloque_de_metodologias_sin_asignadas_avisa():
    from services import prompt

    block = prompt.methodology_assignment_block(ap.get_profile("agent_support"), [])
    assert "Tu perfil es `agent_support`." in block
    assert "no hay metodologías listadas para ti" in block


def test_bloque_guardian_declara_que_ve_todas():
    from services import prompt

    block = prompt.methodology_assignment_block(ap.get_profile("agent_methodologies"), [])
    assert "guardián" in block


def test_bloque_l1_l3_lista_plana_con_etiquetas_de_seccion_y_compartida():
    from services import prompt

    assigned = [
        {"id": "met-1", "title": "Uno", "section_ids": [], "shared": True},
        {"id": "met-2", "title": "Dos", "section_ids": ["sec-1", "sec-9"], "shared": False},
    ]
    block = prompt.methodology_assignment_block(
        ap.get_profile("agent_orchestrator"), assigned, section_labels={"sec-1": "Competencias"}
    )
    assert "- met-1: Uno (compartida)" in block
    assert "- met-2: Dos [Competencias]" in block


def test_bloque_l2_agrupa_por_seccion_y_deja_compartidas_aparte():
    from services import prompt

    assigned = [
        {"id": "met-1", "title": "Uno", "section_ids": [], "shared": True},
        {"id": "met-3", "title": "Tres", "section_ids": ["sec-10"], "shared": False},
        {"id": "met-2", "title": "Dos", "section_ids": ["sec-2"], "shared": False},
    ]
    block = prompt.methodology_assignment_block(
        ap.get_profile("agent_professional_identity"), assigned, section_labels={"sec-2": "Dos"}
    )
    assert block.index("Sección sec-2 · Dos:") < block.index("Sección sec-10 · sec-10:")
    assert "Compartidas (todas las secciones):" in block and "- met-1: Uno" in block


def test_bloque_instruye_leer_metodologias_por_rest_sin_search_knowledge_base():
    from services import prompt

    l2 = prompt.methodology_assignment_block(ap.get_profile("agent_professional_identity"), [])
    assert "list_career_record" in l2 and "operational-methodologies" in l2
    assert "search_knowledge_base" not in l2
    no_read = prompt.methodology_assignment_block(ap.get_profile("agent_task_manager"), [])
    assert "No puedes leer metodologías" in no_read and "search_knowledge_base" not in no_read


def test_bloque_de_memoria_y_de_delegacion():
    from services import prompt

    assert "Ahora mismo no hay ninguna" in prompt._agent_memory_block([])
    mem = prompt._agent_memory_block([{"text": " uno "}, {"text": "  "}, {"text": "dos"}])
    assert "- uno" in mem and "- dos" in mem and mem.count("- ") == 2
    orch = ap.get_profile("agent_orchestrator")
    assert "Especialistas a los que puedes delegar" in prompt._delegation_catalog_block(orch)
    only = prompt._delegation_catalog_block(orch, ["agent_support", "nope"])
    assert "agent_support" in only and "nope" not in only
    assert "no tiene especialistas" in prompt._delegation_catalog_block(orch, [])


async def test_compose_usa_defaults_sin_overrides(pg_db):
    from services import prompt

    async with pg_db() as s:
        text = await prompt.compose_system_prompt(s, ap.get_profile("agent_support"), None)
    assert text.startswith(prompt.default_system_prompt())
    assert prompt.GROUNDING_RULE in text
    assert ap.get_profile("agent_support").system_prompt_suffix in text
    assert prompt._L2_DOMAIN_RULE in text


async def test_compose_respeta_overrides_de_bd_y_sufijo_de_perfil(pg_db):
    from repositories import profile_repo, settings_repo
    from services import prompt

    async with pg_db() as s:
        await settings_repo.set_system_prompt(s, "BASE PROPIA")
        await settings_repo.set_global_rules(s, "REGLAS PROPIAS")
        await profile_repo.set_prompt_suffix(s, "agent_support", "SUFIJO PROPIO")
        text = await prompt.compose_system_prompt(s, ap.get_profile("agent_support"), None)
    assert text.startswith("BASE PROPIA")
    assert "REGLAS PROPIAS" in text and prompt.GROUNDING_RULE not in text
    assert "SUFIJO PROPIO" in text
    assert ap.get_profile("agent_support").system_prompt_suffix not in text


async def test_compose_incluye_metodologias_memoria_pagina_y_reglas_por_nivel(pg_db):
    from services import prompt

    async with pg_db() as s:
        orch = await prompt.compose_system_prompt(
            s, ap.get_profile("agent_orchestrator"),
            {"resource_key": "vacancies", "page_title": "Vacantes", "route": "/job-discovery"},
            assigned=[{"id": "met-1", "title": "Uno", "section_ids": [], "shared": True}],
            notes=[{"text": "recuerda X"}],
            delegate_ids=["agent_support"],
        )
        l3 = await prompt.compose_system_prompt(s, ap.get_profile("agent_changelog"), None, notes=[{"text": "no"}])
        disc = await prompt.compose_system_prompt(s, ap.get_profile("agent_vacancy_search"), None)
    assert "met-1: Uno" in orch and "recuerda X" in orch
    assert "El usuario está en Vacantes (resource_key=vacancies)" in orch
    assert prompt._L1_ORCHESTRATION_RULE in orch and "agent_support (L2)" in orch
    assert prompt.JOB_DISCOVERY_AUTH_RULE in orch  # por ruta
    assert prompt._L3_TASK_RULE in l3 and "recuerda" not in l3 and "MEMORIA PROPIA" not in l3  # L3 sin memoria
    assert prompt.JOB_DISCOVERY_AUTH_RULE in disc  # por perfil


def test_d28_perfiles_con_lectura_reciben_la_instruccion_rest_acotada():
    from services import prompt

    for pid in ("agent_pdf_design", "agent_settings", "agent_configuration", "agent_visual_design"):
        block = prompt.methodology_assignment_block(ap.get_profile(pid), [])
        assert "list_career_record" in block and "get_career_record" in block, pid
        assert "operational-methodologies" in block, pid
        assert "No puedes leer metodologías" not in block, pid
        assert "search_knowledge_base" not in block, pid
