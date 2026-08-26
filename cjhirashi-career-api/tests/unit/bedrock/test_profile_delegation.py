"""Destinos de delegación: subset por nivel + override."""
from services.bedrock.agent_profiles import (
    AGENT_CHANGELOG,
    AGENT_CV_WRITING,
    AGENT_ORCHESTRATOR,
    AGENT_PDF_DESIGN,
    AGENT_PDF_RENDER,
    AGENT_PROFESSIONAL_IDENTITY,
    AGENT_SEARCH_OPERATIONS,
    delegation_error,
    get_profile,
)
from services.bedrock.profile_delegation import default_delegation_ids, filter_level_allowed


def test_filter_drops_same_level_and_unknown():
    l2 = get_profile(AGENT_PDF_DESIGN)
    kept = filter_level_allowed(
        l2,
        [AGENT_PDF_RENDER, AGENT_SEARCH_OPERATIONS, "nope", AGENT_CHANGELOG],
    )
    assert kept == [AGENT_PDF_RENDER, AGENT_CHANGELOG]


def test_orchestrator_defaults_include_l2_and_l3():
    ids = default_delegation_ids(get_profile(AGENT_ORCHESTRATOR))
    assert AGENT_PROFESSIONAL_IDENTITY in ids
    assert AGENT_CV_WRITING in ids
    assert AGENT_ORCHESTRATOR not in ids


def test_delegation_error_honors_configured_subset():
    l2 = get_profile(AGENT_PDF_DESIGN)
    assert delegation_error(l2, AGENT_PDF_RENDER) is None
    assert delegation_error(l2, AGENT_PDF_RENDER, allowed_ids={AGENT_CHANGELOG})
    assert "configured targets" in delegation_error(
        l2, AGENT_PDF_RENDER, allowed_ids={AGENT_CHANGELOG}
    )
