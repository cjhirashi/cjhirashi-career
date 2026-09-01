"""Global rules override (`bedrock_settings.global_rules`) — same pattern as
`system_prompt`: NULL/empty = built-in default, override = total replacement
(not additive). Covers the prompt-composition layer (`services/bedrock/prompt.py`
and `services/bedrock_service.py`) and the `/bedrock/instructions` +
`/bedrock/global-rules` endpoints (`routes/bedrock.py`).
"""
from unittest.mock import MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from services.bedrock import prompt
from services.bedrock.agent_profiles import AGENT_PDF_DESIGN, get_profile
from services.bedrock.prompt import (
    GROUNDING_RULE,
    _METHODOLOGY_ASSIGNMENT_RULE,
    default_global_rules,
)


@pytest.fixture
async def settings_db_session():
    """A SQLite in-memory session with only `bedrock_settings` created -
    avoids the Postgres-only `JSONB` columns other models use, which SQLite
    can't compile (see e.g. `bedrock_agent_delegation`). The shared `db_session`
    fixture in conftest.py creates every model's table via `Base.metadata`."""
    from models.bedrock_settings import BedrockSettings

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(BedrockSettings.__table__.create)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


# ============================================================================
# default_global_rules / get_global_rules_override
# ============================================================================

def test_default_global_rules_combines_grounding_and_methodology_rule():
    text = default_global_rules()
    assert GROUNDING_RULE in text
    assert _METHODOLOGY_ASSIGNMENT_RULE in text
    # Grounding first, methodology second - same order the old hardcoded
    # `parts` list had (GROUNDING_RULE, then methodology_assignment_block()).
    assert text.index(GROUNDING_RULE) < text.index(_METHODOLOGY_ASSIGNMENT_RULE)


def test_methodology_assignment_block_no_longer_repeats_the_rule():
    """The rule now lives only in default_global_rules(); the block itself
    should not duplicate it as its first line."""
    block = prompt.methodology_assignment_block(get_profile(AGENT_PDF_DESIGN), [])
    assert block.startswith("Tu perfil es `agent_pdf_design`.")
    assert _METHODOLOGY_ASSIGNMENT_RULE not in block


@pytest.mark.asyncio
async def test_get_global_rules_override_none_when_no_row(settings_db_session):
    result = await prompt.get_global_rules_override(settings_db_session)
    assert result is None


@pytest.mark.asyncio
async def test_get_global_rules_override_returns_saved_text(settings_db_session):
    from services import bedrock_service

    await bedrock_service.set_global_rules(settings_db_session, "Regla global custom de Carlos.")
    result = await prompt.get_global_rules_override(settings_db_session)
    assert result == "Regla global custom de Carlos."


# ============================================================================
# compose_system_prompt — usa el override fresco, no concatena
# ============================================================================

@pytest.mark.asyncio
async def test_compose_uses_default_global_rules_without_override(monkeypatch):
    async def fake_system_prompt_override(_db):
        return None

    async def fake_global_rules_override(_db):
        return None

    async def fake_suffix(_db, profile):
        return profile.system_prompt_suffix

    monkeypatch.setattr(prompt, "get_system_prompt_override", fake_system_prompt_override)
    monkeypatch.setattr(prompt, "get_global_rules_override", fake_global_rules_override)
    monkeypatch.setattr(prompt.profile_prompts, "get_effective_suffix", fake_suffix)

    composed = await prompt.compose_system_prompt(
        MagicMock(), get_profile(AGENT_PDF_DESIGN), None,
    )
    assert GROUNDING_RULE in composed
    assert _METHODOLOGY_ASSIGNMENT_RULE in composed


@pytest.mark.asyncio
async def test_compose_uses_override_and_replaces_not_concatenates(monkeypatch):
    custom_rules = "SOLO regla custom — reemplaza por completo el default."

    async def fake_system_prompt_override(_db):
        return None

    async def fake_global_rules_override(_db):
        return custom_rules

    async def fake_suffix(_db, profile):
        return profile.system_prompt_suffix

    monkeypatch.setattr(prompt, "get_system_prompt_override", fake_system_prompt_override)
    monkeypatch.setattr(prompt, "get_global_rules_override", fake_global_rules_override)
    monkeypatch.setattr(prompt.profile_prompts, "get_effective_suffix", fake_suffix)

    composed = await prompt.compose_system_prompt(
        MagicMock(), get_profile(AGENT_PDF_DESIGN), None,
    )
    assert custom_rules in composed
    # Total replacement, not additive: the default rules must be gone.
    assert GROUNDING_RULE not in composed
    assert _METHODOLOGY_ASSIGNMENT_RULE not in composed


@pytest.mark.asyncio
async def test_compose_reads_global_rules_override_fresh_each_call(monkeypatch, settings_db_session):
    from services import bedrock_service

    async def fake_system_prompt_override(_db):
        return None

    async def fake_suffix(_db, profile):
        return profile.system_prompt_suffix

    monkeypatch.setattr(prompt, "get_system_prompt_override", fake_system_prompt_override)
    monkeypatch.setattr(prompt.profile_prompts, "get_effective_suffix", fake_suffix)

    profile = get_profile(AGENT_PDF_DESIGN)

    first = await prompt.compose_system_prompt(settings_db_session, profile, None)
    assert GROUNDING_RULE in first

    await bedrock_service.set_global_rules(settings_db_session, "Regla nueva tras el primer turno.")

    second = await prompt.compose_system_prompt(settings_db_session, profile, None)
    assert "Regla nueva tras el primer turno." in second
    assert GROUNDING_RULE not in second


# ============================================================================
# services/bedrock_service.py — default_global_rules / get / set
# ============================================================================

@pytest.mark.asyncio
async def test_service_get_global_rules_defaults_when_no_row(settings_db_session):
    from services import bedrock_service

    result = await bedrock_service.get_global_rules(settings_db_session)
    assert result == bedrock_service.default_global_rules()


@pytest.mark.asyncio
async def test_service_set_global_rules_then_clear_resets_to_default(settings_db_session):
    from services import bedrock_service

    custom = "Nueva regla global desde el Admin."
    updated = await bedrock_service.set_global_rules(settings_db_session, custom)
    assert updated == custom

    cleared = await bedrock_service.set_global_rules(settings_db_session, None)
    assert cleared == bedrock_service.default_global_rules()


# ============================================================================
# routes/bedrock.py — GET/PUT /instructions, PUT /global-rules
# ============================================================================

@pytest.mark.asyncio
async def test_get_instructions_returns_both_defaults(settings_db_session):
    from routes import bedrock as bedrock_routes

    response = await bedrock_routes.get_instructions(current_user=MagicMock(), db=settings_db_session)
    assert response.system_prompt_is_default is True
    assert response.global_rules_is_default is True
    assert response.global_rules == default_global_rules()


@pytest.mark.asyncio
async def test_put_instructions_only_touches_system_prompt(settings_db_session):
    from routes import bedrock as bedrock_routes
    from schemas.bedrock import BedrockGlobalRulesUpdateRequest, BedrockInstructionsUpdateRequest

    await bedrock_routes.update_global_rules(
        BedrockGlobalRulesUpdateRequest(global_rules="Regla global fijada antes."),
        current_user=MagicMock(),
        db=settings_db_session,
    )

    response = await bedrock_routes.update_instructions(
        BedrockInstructionsUpdateRequest(system_prompt="Prompt base custom."),
        current_user=MagicMock(),
        db=settings_db_session,
    )
    assert response.system_prompt == "Prompt base custom."
    assert response.system_prompt_is_default is False
    # global_rules untouched by this endpoint, but still reported.
    assert response.global_rules == "Regla global fijada antes."
    assert response.global_rules_is_default is False


@pytest.mark.asyncio
async def test_put_global_rules_updates_and_reports_full_state(settings_db_session):
    from routes import bedrock as bedrock_routes
    from schemas.bedrock import BedrockGlobalRulesUpdateRequest

    response = await bedrock_routes.update_global_rules(
        BedrockGlobalRulesUpdateRequest(global_rules="Nueva regla global."),
        current_user=MagicMock(),
        db=settings_db_session,
    )
    assert response.global_rules == "Nueva regla global."
    assert response.global_rules_is_default is False
    # system_prompt untouched, still default.
    assert response.system_prompt_is_default is True


@pytest.mark.asyncio
async def test_put_global_rules_empty_string_resets_to_default(settings_db_session):
    from routes import bedrock as bedrock_routes
    from schemas.bedrock import BedrockGlobalRulesUpdateRequest

    await bedrock_routes.update_global_rules(
        BedrockGlobalRulesUpdateRequest(global_rules="temporal"),
        current_user=MagicMock(),
        db=settings_db_session,
    )
    response = await bedrock_routes.update_global_rules(
        BedrockGlobalRulesUpdateRequest(global_rules=None),
        current_user=MagicMock(),
        db=settings_db_session,
    )
    assert response.global_rules_is_default is True
    assert response.global_rules == default_global_rules()
