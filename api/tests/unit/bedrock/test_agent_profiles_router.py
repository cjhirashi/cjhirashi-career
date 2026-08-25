"""Tests unitarios Bedrock harness."""
import pytest
from services.bedrock.agent_profiles import resolve_agent_profile, get_profile
from services.bedrock.tools import converse_tool_specs, all_tool_names


def test_resolve_digital_route():
    profile = resolve_agent_profile(
        chat_surface="contextual",
        agent_profile_id=None,
        page_context={"route": "/linkedin", "resource_key": "linkedin-posts"},
    )
    assert profile.id == "digital"


def test_general_chat_is_orchestrator():
    profile = resolve_agent_profile(chat_surface="general", agent_profile_id=None, page_context=None)
    assert profile.id == "orchestrator"


def test_digital_tools_exclude_delegate():
    from services.bedrock.agent_profiles import tools_for_profile

    names = tools_for_profile(get_profile("digital"), all_tool_names())
    assert "delegate_to_specialist" not in names
    assert "create_linkedin_post" in names
    assert "run_job_discovery" not in names


def test_search_route_and_job_tools():
    from services.bedrock.agent_profiles import tools_for_profile

    profile = resolve_agent_profile(
        chat_surface="contextual",
        agent_profile_id=None,
        page_context={"route": "/job-discovery"},
    )
    assert profile.id == "search"
    names = tools_for_profile(profile, all_tool_names())
    assert "run_job_discovery" in names
    assert "import_job_url" in names
    assert "save_job_listings" in names


def test_converse_tool_specs_subset():
    allowed = {"list_career_record", "get_career_record"}
    specs = converse_tool_specs(allowed)
    assert len(specs) == 2
    assert specs[0]["toolSpec"]["name"] in allowed


def test_pdf_design_has_separate_template_and_style_tools():
    from services.bedrock.agent_profiles import tools_for_profile
    from services.bedrock.tools import all_tool_names

    names = tools_for_profile(get_profile("pdf_design"), all_tool_names())
    assert "pdf_template" in names
    assert "pdf_style" in names
    assert "generate_pdf" in names
    assert "list_pdf_templates" not in names
    assert "create_pdf_template_style" not in names
    assert "delegate_to_specialist" not in names


def test_identity_cannot_use_pdf_tools():
    from services.bedrock.agent_profiles import tools_for_profile
    from services.bedrock.tools import all_tool_names

    names = tools_for_profile(get_profile("identity"), all_tool_names())
    assert "pdf_template" not in names
    assert "pdf_style" not in names
    assert "generate_pdf" not in names


def test_pdf_admin_routes_resolve_to_pdf_design():
    for route in ("/agent/pdf-templates", "/agent/pdf-template-styles"):
        profile = resolve_agent_profile(
            chat_surface="contextual",
            agent_profile_id=None,
            page_context={"route": route},
        )
        assert profile.id == "pdf_design"


def test_history_manager_filters_by_agent_profile():
    import inspect
    from services.bedrock.history_manager import get_or_create_conversation, list_conversations

    assert "agent_profile_id" in inspect.signature(get_or_create_conversation).parameters
    assert "agent_profile_id" in inspect.signature(list_conversations).parameters
