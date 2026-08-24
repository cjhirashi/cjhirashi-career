"""Tests unitarios Harness local Bedrock."""
import pytest
from services.bedrock.agent_profiles import resolve_agent_profile, get_profile
from services.bedrock.tools import converse_tool_specs, all_tool_names
from services.bedrock.agent_loop import use_local_harness


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
