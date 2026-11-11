"""Metodologías asignadas al agente se inyectan en el system prompt (no hardcoded)."""
from unittest.mock import MagicMock

import pytest

from services.bedrock.agent_profiles import (
    AGENT_CV_WRITING,
    AGENT_METHODOLOGIES,
    AGENT_ORCHESTRATOR,
    AGENT_PDF_DESIGN,
    AGENT_PDF_RENDER,
    AGENT_PROFESSIONAL_IDENTITY,
    get_profile,
    list_profiles,
)
from services.bedrock.prompt import methodology_assignment_block
from services.bedrock_service import default_system_prompt


def test_assignment_block_lists_assigned_titles_not_hardcoded_section():
    profile = get_profile(AGENT_PDF_DESIGN)
    block = methodology_assignment_block(
        profile,
        [
            {
                "id": "opm-99",
                "title": "Nueva convención de márgenes",
                "section": "Diseño PDF",
                "shared": False,
            },
            {
                "id": "opm-1",
                "title": "Protocolo compartido",
                "section": None,
                "shared": True,
            },
        ],
    )
    # La regla "solo las asignadas a ti" ahora vive en default_global_rules()
    # (ver test_global_rules.py), no en el bloque de catálogo en sí.
    # spec 004: para un L2 el catálogo se agrupa por sección de procedencia;
    # sin section_ids, las metodologías caen en el grupo "Compartidas".
    assert "`agent_pdf_design`" in block
    assert "opm-99: Nueva convención de márgenes" in block
    assert "opm-1: Protocolo compartido" in block
    assert "Compartidas" in block


def test_assignment_block_empty_catalog_still_instructs_to_consult_future_ones():
    block = methodology_assignment_block(get_profile(AGENT_PROFESSIONAL_IDENTITY), [])
    assert "`agent_professional_identity`" in block
    assert "Cuando Carlos te asigne una desde el Admin" in block


def test_guardian_sees_all_and_assigns():
    block = methodology_assignment_block(get_profile(AGENT_METHODOLOGIES), [])
    assert "guardián" in block
    assert "agent_profile_ids" in block


def test_every_profile_gets_assignment_block_starting_with_its_id():
    """The global "solo las asignadas a ti" rule itself is now shared across
    all profiles via default_global_rules() (see test_global_rules.py); this
    block only carries the per-profile catalog framing."""
    for profile in list_profiles():
        block = methodology_assignment_block(profile, None)
        assert block.startswith(f"Tu perfil es `{profile.id}`.")


def test_pdf_suffix_does_not_hardcode_section_as_search_target():
    suffix = get_profile(AGENT_PDF_DESIGN).system_prompt_suffix
    assert "en «Diseño PDF»" not in suffix
    assert "asignadas a este perfil" in suffix


def test_default_prompt_consults_only_assigned_methodologies():
    text = default_system_prompt()
    assert "metodologías operativas asignadas a tu perfil" in text
    assert "agent_profile_ids" in text
    assert "también son tuyas para mantener" not in text


@pytest.mark.asyncio
async def test_compose_injects_assigned_catalog(monkeypatch):
    from services.bedrock import prompt

    async def fake_override(_db):
        return None

    async def fake_global_rules_override(_db):
        return None

    async def fake_suffix(_db, profile):
        return profile.system_prompt_suffix

    async def fake_list(_db, _user_id, caller_id, caller_section_ids=None):
        assert caller_id == AGENT_PDF_DESIGN
        return [
            {
                "id": "opm-88",
                "title": "Metodología recién asignada",
                "section": "Calidad",
                "section_ids": ["sec-58"],
                "shared": False,
            }
        ]

    monkeypatch.setattr(prompt, "get_system_prompt_override", fake_override)
    monkeypatch.setattr(prompt, "get_global_rules_override", fake_global_rules_override)
    monkeypatch.setattr(prompt.profile_prompts, "get_effective_suffix", fake_suffix)
    monkeypatch.setattr(
        "services.methodology_scope.list_assigned_methodologies",
        fake_list,
    )

    composed = await prompt.compose_system_prompt(
        MagicMock(),
        get_profile(AGENT_PDF_DESIGN),
        None,
        user_id="usr-1",
    )
    assert "opm-88: Metodología recién asignada" in composed
    assert "Sección sec-58" in composed  # spec 004: agrupado por sección para L2
    assert "solo las asignadas a ti" in composed
    assert "metodologías operativas asignadas a tu perfil" in composed


@pytest.mark.requisito("RF-008")
def test_l2_block_groups_methodologies_by_section():
    from services.bedrock.prompt import methodology_assignment_block

    profile = get_profile(AGENT_PROFESSIONAL_IDENTITY)  # L2
    assigned = [
        {"id": "opm-1", "title": "Proceso Portafolio", "section": "Identidad", "section_ids": ["sec-32"], "shared": False},
        {"id": "opm-2", "title": "Proceso Competencias", "section": "Identidad", "section_ids": ["sec-32"], "shared": False},
        {"id": "opm-9", "title": "Mapa de tablas", "section": "Bóveda", "section_ids": [], "shared": True},
    ]
    block = methodology_assignment_block(profile, assigned)
    assert "Sección sec-32" in block
    assert "opm-1: Proceso Portafolio" in block
    assert "opm-2: Proceso Competencias" in block
    assert "Compartidas" in block and "opm-9: Mapa de tablas" in block


@pytest.mark.requisito("RF-008")
def test_l3_block_stays_flat():
    from services.bedrock.prompt import methodology_assignment_block

    profile = get_profile(AGENT_PDF_RENDER)  # L3
    assigned = [{"id": "opm-5", "title": "Weasy", "section": "Infra", "section_ids": [], "shared": False}]
    block = methodology_assignment_block(profile, assigned)
    assert "Sección sec-" not in block
    assert "opm-5: Weasy" in block
