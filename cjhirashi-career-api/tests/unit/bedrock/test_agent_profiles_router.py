"""Tests unitarios Bedrock harness."""
from services.bedrock.agent_profiles import (
    AGENT_CHANGELOG,
    AGENT_DIGITAL_PRESENCE,
    AGENT_LINKEDIN_PUBLISHING,
    AGENT_ORCHESTRATOR,
    AGENT_PDF_DESIGN,
    AGENT_PDF_RENDER,
    AGENT_PROFESSIONAL_IDENTITY,
    AGENT_SEARCH_OPERATIONS,
    AGENT_TASK_MANAGER,
    AGENT_VACANCY_SEARCH,
    AGENT_CV_WRITING,
    AGENT_COVER_LETTER_WRITING,
    AGENT_VISUAL_DESIGN,
    AGENT_WEB_SEARCH,
    AGENT_GITHUB,
    AGENT_SETTINGS,
    can_delegate_to,
    delegation_error,
    get_profile,
    list_profiles,
    list_user_facing_profiles,
    resolve_agent_profile,
    tools_for_profile,
)
from services.bedrock.tools import converse_tool_specs, all_tool_names


def test_unknown_profile_raises_keyerror():
    import pytest

    with pytest.raises(KeyError):
        get_profile("orchestrator")
    with pytest.raises(KeyError):
        get_profile("identity")


def test_resolve_digital_route():
    profile = resolve_agent_profile(
        chat_surface="contextual",
        agent_profile_id=None,
        page_context={"route": "/linkedin", "resource_key": "linkedin-posts"},
    )
    assert profile.id == AGENT_DIGITAL_PRESENCE


def test_general_chat_is_orchestrator():
    profile = resolve_agent_profile(chat_surface="general", agent_profile_id=None, page_context=None)
    assert profile.id == AGENT_ORCHESTRATOR
    assert profile.level == 1


def test_digital_tools_include_delegate_to_l3():
    names = tools_for_profile(get_profile(AGENT_DIGITAL_PRESENCE), all_tool_names())
    assert "delegate_to_specialist" in names
    assert "create_linkedin_post" not in names
    assert "list_linkedin_posts" not in names
    assert "run_job_discovery" not in names
    assert "generate_pdf" not in names
    assert "list_recent_changes" not in names


def test_linkedin_publishing_is_l3():
    profile = get_profile(AGENT_LINKEDIN_PUBLISHING)
    assert profile.level == 3
    assert not profile.user_facing
    names = tools_for_profile(profile, all_tool_names())
    assert "create_linkedin_post" in names
    assert "list_linkedin_posts" in names
    assert "get_linkedin_status" in names
    assert "delete_scheduled_linkedin_post" in names
    assert "delegate_to_specialist" not in names
    assert "create_career_record" not in names


def test_search_route_and_job_tools():
    profile = resolve_agent_profile(
        chat_surface="contextual",
        agent_profile_id=None,
        page_context={"route": "/job-discovery"},
    )
    assert profile.id == AGENT_SEARCH_OPERATIONS
    names = tools_for_profile(profile, all_tool_names())
    assert "run_job_discovery" not in names
    assert "save_job_listings" not in names
    assert "delegate_to_specialist" in names
    assert "generate_pdf" not in names
    assert "list_career_record" in names


def test_vacancy_search_is_l3():
    profile = get_profile(AGENT_VACANCY_SEARCH)
    assert profile.level == 3
    assert not profile.user_facing
    names = tools_for_profile(profile, all_tool_names())
    assert "run_job_discovery" in names
    assert "import_job_url" in names
    assert "save_job_listings" in names
    assert "list_job_providers" in names
    assert "delegate_to_specialist" not in names
    assert "create_career_record" not in names


def test_cv_writing_is_l3():
    profile = get_profile(AGENT_CV_WRITING)
    assert profile.level == 3
    assert not profile.user_facing
    assert profile.resource_keys == ["cv-versions"]
    names = tools_for_profile(profile, all_tool_names())
    assert "create_career_record" in names
    assert "update_career_record" in names
    assert "search_knowledge_base" in names
    assert "generate_pdf" not in names
    assert "render_record_pdf" not in names
    assert "delegate_to_specialist" not in names
    assert "run_job_discovery" not in names


def test_cover_letter_writing_is_l3():
    profile = get_profile(AGENT_COVER_LETTER_WRITING)
    assert profile.level == 3
    assert not profile.user_facing
    assert profile.resource_keys == ["cover-letter-versions"]
    names = tools_for_profile(profile, all_tool_names())
    assert "create_career_record" in names
    assert "generate_pdf" not in names
    assert "delegate_to_specialist" not in names


def test_converse_tool_specs_subset():
    allowed = {"list_career_record", "get_career_record"}
    specs = converse_tool_specs(allowed)
    assert len(specs) == 2
    assert specs[0]["toolSpec"]["name"] in allowed


def test_pdf_design_owns_templates_not_render():
    names = tools_for_profile(get_profile(AGENT_PDF_DESIGN), all_tool_names())
    assert "pdf_template" in names
    assert "pdf_style" in names
    assert "delegate_to_specialist" in names
    assert "generate_pdf" not in names
    assert "render_record_pdf" not in names
    assert "list_pdf_templates" not in names
    assert "create_pdf_template_style" not in names


def test_pdf_render_is_l3_with_render_tools():
    profile = get_profile(AGENT_PDF_RENDER)
    assert profile.level == 3
    assert not profile.user_facing
    names = tools_for_profile(profile, all_tool_names())
    assert "generate_pdf" in names
    assert "render_record_pdf" in names
    assert "list_pdf_capable_resources" in names
    assert "pdf_template" not in names
    assert "delegate_to_specialist" not in names


def test_personal_profile_routes_to_identity():
    profile = resolve_agent_profile(
        chat_surface="contextual",
        agent_profile_id=None,
        page_context={"route": "/career/personal-profile", "resource_key": "personal-profile"},
    )
    assert profile.id == AGENT_PROFESSIONAL_IDENTITY
    assert "personal-profile" in (profile.resource_keys or [])
    assert "personal-profile" in profile.system_prompt_suffix


def test_identity_cannot_use_pdf_tools():
    names = tools_for_profile(get_profile(AGENT_PROFESSIONAL_IDENTITY), all_tool_names())
    assert "pdf_template" not in names
    assert "pdf_style" not in names
    assert "generate_pdf" not in names


def test_pdf_admin_routes_resolve_to_pdf_design():
    for route in (
        "/agent/pdf-templates",
        "/agent/pdf-template-styles",
        "/agent/pdf-templates/cv-ats-optimizado",
        "/agent/pdf-template-styles/pds-cyan",
    ):
        profile = resolve_agent_profile(
            chat_surface="contextual",
            agent_profile_id=None,
            page_context={"route": route},
        )
        assert profile.id == AGENT_PDF_DESIGN
        assert profile.level == 2


def test_settings_routes_resolve_to_agent_settings():
    for route in (
        "/settings/agents",
        "/settings/agents/agent-2",
        "/settings/sections",
        "/settings/sections/sec-1",
        "/settings/agent-prompts",
    ):
        profile = resolve_agent_profile(
            chat_surface="contextual",
            agent_profile_id=None,
            page_context={"route": route},
        )
        assert profile.id == AGENT_SETTINGS
        assert profile.level == 2


def test_agent_settings_owns_its_tools_only():
    names = tools_for_profile(get_profile(AGENT_SETTINGS), all_tool_names())
    assert "agent_catalog_settings" in names
    assert "admin_section_settings" in names
    assert "bedrock_global_settings" in names
    assert "create_career_record" not in names
    assert "delegate_to_specialist" in names


def test_history_manager_filters_by_agent_profile():
    import inspect
    from services.bedrock.history_manager import get_or_create_conversation, list_conversations

    assert "agent_profile_id" in inspect.signature(get_or_create_conversation).parameters
    assert "agent_profile_id" in inspect.signature(list_conversations).parameters


def test_orchestrator_has_only_delegate_tool():
    names = tools_for_profile(get_profile(AGENT_ORCHESTRATOR), all_tool_names())
    assert names == {"delegate_to_specialist"}


def test_delegation_is_downward_only():
    l1 = get_profile(AGENT_ORCHESTRATOR)
    l2 = get_profile(AGENT_PROFESSIONAL_IDENTITY)
    l3 = get_profile(AGENT_PDF_RENDER)
    search = get_profile(AGENT_SEARCH_OPERATIONS)

    assert can_delegate_to(l1, l2)
    assert can_delegate_to(l1, l3)
    assert can_delegate_to(l2, l3)
    assert can_delegate_to(get_profile(AGENT_DIGITAL_PRESENCE), get_profile(AGENT_LINKEDIN_PUBLISHING))
    assert can_delegate_to(search, get_profile(AGENT_VACANCY_SEARCH))
    assert can_delegate_to(search, get_profile(AGENT_CV_WRITING))
    assert can_delegate_to(search, get_profile(AGENT_COVER_LETTER_WRITING))
    assert not can_delegate_to(l2, l1)
    assert not can_delegate_to(l2, search)
    assert not can_delegate_to(l3, l1)
    assert not can_delegate_to(l3, l2)
    assert not can_delegate_to(l3, get_profile(AGENT_CHANGELOG))

    assert delegation_error(l2, AGENT_ORCHESTRATOR)
    assert delegation_error(l2, AGENT_SEARCH_OPERATIONS)
    assert delegation_error(l1, AGENT_PROFESSIONAL_IDENTITY) is None
    assert delegation_error(l2, AGENT_CHANGELOG) is None
    assert delegation_error(l1, "unknown_agent") == "unknown agent profile: unknown_agent"


def test_user_facing_profiles_exclude_l3():
    facing = {p.id for p in list_user_facing_profiles()}
    assert AGENT_ORCHESTRATOR in facing
    assert AGENT_PDF_DESIGN in facing
    assert AGENT_PDF_RENDER not in facing
    assert AGENT_VISUAL_DESIGN not in facing
    assert AGENT_CHANGELOG not in facing
    assert AGENT_TASK_MANAGER not in facing
    assert AGENT_LINKEDIN_PUBLISHING not in facing
    assert AGENT_VACANCY_SEARCH not in facing
    assert AGENT_CV_WRITING not in facing
    assert AGENT_COVER_LETTER_WRITING not in facing
    assert AGENT_WEB_SEARCH not in facing
    assert AGENT_GITHUB not in facing
    assert all(p.level in (1, 2) for p in list_user_facing_profiles())
    assert any(p.level == 3 for p in list_profiles())


def test_delegate_spec_lists_allowed_targets():
    specs = converse_tool_specs({"delegate_to_specialist"}, caller_profile=get_profile(AGENT_SEARCH_OPERATIONS))
    description = specs[0]["toolSpec"]["description"]
    assert AGENT_PDF_RENDER in description
    assert AGENT_VACANCY_SEARCH in description
    assert AGENT_CV_WRITING in description
    assert AGENT_COVER_LETTER_WRITING in description
    assert AGENT_WEB_SEARCH in description
    assert AGENT_GITHUB in description
    assert AGENT_PROFESSIONAL_IDENTITY not in description


def test_visual_design_is_l3():
    profile = get_profile(AGENT_VISUAL_DESIGN)
    assert profile.level == 3
    names = tools_for_profile(profile, all_tool_names())
    assert "generate_image" in names
    assert "delegate_to_specialist" not in names


def test_pdf_capable_resources_cover_cv_and_cover_letter():
    from services.bedrock.tools import PDF_CAPABLE_RESOURCES

    assert "cv-versions" in PDF_CAPABLE_RESOURCES
    assert PDF_CAPABLE_RESOURCES["cv-versions"]["content_attr"] == "content"
    assert PDF_CAPABLE_RESOURCES["cover-letter-versions"]["content_attr"] == "body_content"


def test_web_search_is_l3_with_web_tools():
    profile = get_profile(AGENT_WEB_SEARCH)
    assert profile.level == 3
    assert not profile.user_facing
    names = tools_for_profile(profile, all_tool_names())
    assert names == {"web_search", "web_fetch"}
    assert "delegate_to_specialist" not in names
    assert "web_search" in profile.system_prompt_suffix
    assert "web_fetch" in profile.system_prompt_suffix


def test_github_is_l3_with_github_tools():
    profile = get_profile(AGENT_GITHUB)
    assert profile.level == 3
    assert not profile.user_facing
    names = tools_for_profile(profile, all_tool_names())
    assert "get_github_status" in names
    assert "list_github_repos" in names
    assert "get_github_file" in names
    assert "search_github_code" in names
    assert "delegate_to_specialist" not in names
    assert "create_career_record" not in names
    assert can_delegate_to(get_profile(AGENT_DIGITAL_PRESENCE), profile)
    assert can_delegate_to(get_profile(AGENT_ORCHESTRATOR), profile)
    assert "agent_github" in get_profile(AGENT_DIGITAL_PRESENCE).system_prompt_suffix
    assert "agent_web_search" in get_profile(AGENT_ORCHESTRATOR).system_prompt_suffix

