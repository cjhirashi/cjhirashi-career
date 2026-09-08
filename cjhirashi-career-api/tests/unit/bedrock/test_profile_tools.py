"""Override de herramientas por perfil (profile_tools)."""
import pytest

from services.bedrock.agent_profiles import (
    AGENT_ORCHESTRATOR,
    AGENT_PROFESSIONAL_IDENTITY,
    AGENT_VISUAL_DESIGN,
    get_profile,
    tools_for_profile,
)
from services.bedrock import tools as bedrock_tools
from services.bedrock.profile_tools import (
    default_tool_names,
    effective_tool_names,
    list_builtin_tool_catalog,
    validate_tool_names,
)


def test_default_tool_names_match_code():
    profile = get_profile(AGENT_PROFESSIONAL_IDENTITY)
    assert default_tool_names(profile) == tools_for_profile(
        profile, bedrock_tools.all_tool_names()
    )


def test_effective_without_override_is_default():
    profile = get_profile(AGENT_PROFESSIONAL_IDENTITY)
    assert effective_tool_names(profile, None) == default_tool_names(profile)


def test_effective_override_replaces_default():
    profile = get_profile(AGENT_PROFESSIONAL_IDENTITY)
    # L2 delega → delegate_to_specialist se añade al override
    assert effective_tool_names(profile, ["list_career_record"]) == {
        "list_career_record",
        "delegate_to_specialist",
    }
    # un tool que el default tenía (search_knowledge_base) ya no está
    assert "search_knowledge_base" not in effective_tool_names(
        profile, ["list_career_record"]
    )


def test_delegate_rule_by_level_after_override():
    l3 = get_profile(AGENT_VISUAL_DESIGN)
    assert l3.level == 3
    # L3 no delega → delegate_to_specialist se descarta aunque esté en el override
    assert "delegate_to_specialist" not in effective_tool_names(
        l3, ["generate_image", "delegate_to_specialist"]
    )
    assert effective_tool_names(l3, ["generate_image"]) == {"generate_image"}


def test_override_ignores_unknown_tool_names():
    profile = get_profile(AGENT_PROFESSIONAL_IDENTITY)
    result = effective_tool_names(profile, ["list_career_record", "not_a_tool"])
    assert "not_a_tool" not in result
    assert "list_career_record" in result


def test_validate_tool_names_normalizes_and_dedupes():
    # tools scope!=section (spec 004): search_knowledge_base + generate_image
    assert validate_tool_names(
        ["generate_image", "search_knowledge_base", "generate_image"]
    ) == ["generate_image", "search_knowledge_base"]


def test_validate_tool_names_rejects_unknown():
    with pytest.raises(ValueError):
        validate_tool_names(["search_knowledge_base", "not_a_tool"])


def test_orchestrator_default_is_delegate_only():
    profile = get_profile(AGENT_ORCHESTRATOR)
    assert default_tool_names(profile) == {"delegate_to_specialist"}
    # D-4: el operador puede añadir tools al L1 desde el override
    assert effective_tool_names(profile, ["list_career_record"]) == {
        "list_career_record",
        "delegate_to_specialist",
    }


def test_list_builtin_tool_catalog_has_name_and_description():
    catalog = list_builtin_tool_catalog()
    assert len(catalog) == len(bedrock_tools.all_tool_names())
    assert all("name" in t and "description" in t for t in catalog)
    names = {t["name"] for t in catalog}
    assert "list_career_record" in names
    assert "search_knowledge_base" in names


# ============================================================================
# Spec 004 — herramientas de L2 vía sección
# ============================================================================
import pytest as _pytest
from unittest.mock import AsyncMock, patch


@_pytest.mark.asyncio
@_pytest.mark.requisito("RF-002")
async def test_resolve_effective_tools_l2_from_sections():
    from services.bedrock import profile_tools

    profile = get_profile(AGENT_PROFESSIONAL_IDENTITY)  # L2
    assert profile.level == 2
    derived = {"list_career_record", "get_career_record", "search_knowledge_base"}

    with patch(
        "services.section_catalog.derived_tools_for_agent",
        new=AsyncMock(return_value=set(derived)),
    ) as d, patch(
        "services.section_catalog.sections_for_agent",
        new=AsyncMock(return_value=[{"id": "sec-32"}, {"id": "sec-6"}]),
    ):
        eff, section_ids = await profile_tools.resolve_effective_tools(db=None, profile=profile)

    d.assert_awaited_once()  # RNF-001: una resolución por turno
    assert derived <= eff
    assert "delegate_to_specialist" in eff  # L2 delega (regla de nivel D-2)
    assert section_ids == ["sec-32", "sec-6"]


@_pytest.mark.asyncio
@_pytest.mark.requisito("RF-004")
async def test_resolve_effective_tools_l3_uses_direct_override():
    from services.bedrock import profile_tools

    profile = get_profile(AGENT_VISUAL_DESIGN)  # L3
    assert profile.level == 3

    with patch(
        "services.bedrock.profile_tools.get_tool_override",
        new=AsyncMock(return_value=["list_career_record"]),
    ), patch(
        "services.section_catalog.derived_tools_for_agent",
        new=AsyncMock(side_effect=AssertionError("L3 no resuelve por sección")),
    ):
        eff, section_ids = await profile_tools.resolve_effective_tools(db=None, profile=profile)

    assert eff == {"list_career_record"}  # L3 no delega
    assert section_ids == []


@_pytest.mark.asyncio
@_pytest.mark.requisito("RF-004")
async def test_resolve_effective_tools_l1_default():
    from services.bedrock import profile_tools

    profile = get_profile(AGENT_ORCHESTRATOR)  # L1

    with patch(
        "services.bedrock.profile_tools.get_tool_override", new=AsyncMock(return_value=None)
    ):
        eff, section_ids = await profile_tools.resolve_effective_tools(db=None, profile=profile)

    assert eff == {"delegate_to_specialist"}
    assert section_ids == []


@_pytest.mark.requisito("RF-011")
def test_validate_tool_names_rejects_section_scope():
    from services.bedrock.profile_tools import validate_tool_names

    # create_career_record es scope=section → no asignable directo a L1/L3
    with _pytest.raises(ValueError):
        validate_tool_names(["create_career_record"])
    # search_knowledge_base es scope=both → permitido
    assert validate_tool_names(["search_knowledge_base"]) == ["search_knowledge_base"]
