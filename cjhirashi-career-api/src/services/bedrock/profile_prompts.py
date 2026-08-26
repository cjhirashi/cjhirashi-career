"""Runtime overrides for agent profile system_prompt_suffix (Admin Panel)."""
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.bedrock_agent_profile_prompt import BedrockAgentProfilePrompt
from services.bedrock.agent_profiles import AgentProfile, get_profile, list_profiles


# ============================================================================
# Overrides de suffix desde PG
# ============================================================================

async def _overrides_map(db: AsyncSession) -> Dict[str, str]:
    result = await db.execute(select(BedrockAgentProfilePrompt))
    return {row.profile_id: row.system_prompt_suffix for row in result.scalars().all()}


# ============================================================================
# Lectura de suffix efectivo
# ============================================================================

async def get_effective_suffix(db: AsyncSession, profile: AgentProfile) -> str:
    result = await db.execute(
        select(BedrockAgentProfilePrompt).where(
            BedrockAgentProfilePrompt.profile_id == profile.id
        )
    )
    row = result.scalar_one_or_none()
    if row and row.system_prompt_suffix.strip():
        return row.system_prompt_suffix.strip()
    return profile.system_prompt_suffix


# ============================================================================
# API de prompts por perfil
# ============================================================================

async def list_profile_prompts(db: AsyncSession) -> List[dict]:
    overrides = await _overrides_map(db)
    items: List[dict] = []
    for profile in list_profiles():
        override = overrides.get(profile.id)
        effective = override if override is not None else profile.system_prompt_suffix
        items.append(
            {
                "profile_id": profile.id,
                "label": profile.label,
                "level": profile.level,
                "user_facing": profile.user_facing,
                "default_suffix": profile.system_prompt_suffix,
                "override_suffix": override,
                "effective_suffix": effective,
                "is_default": override is None,
            }
        )
    return items


async def set_profile_prompt_suffix(
    db: AsyncSession,
    profile_id: str,
    system_prompt_suffix: Optional[str],
) -> dict:
    profile = get_profile(profile_id)
    profile_id = profile.id
    text = system_prompt_suffix.strip() if system_prompt_suffix else None

    result = await db.execute(
        select(BedrockAgentProfilePrompt).where(
            BedrockAgentProfilePrompt.profile_id == profile_id
        )
    )
    row = result.scalar_one_or_none()

    if not text:
        if row:
            await db.delete(row)
        await db.commit()
    elif row:
        row.system_prompt_suffix = text
        await db.commit()
        await db.refresh(row)
    else:
        db.add(BedrockAgentProfilePrompt(profile_id=profile_id, system_prompt_suffix=text))
        await db.commit()

    profile = get_profile(profile_id)
    overrides = await _overrides_map(db)
    override = overrides.get(profile.id)
    return {
        "profile_id": profile.id,
        "label": profile.label,
        "level": profile.level,
        "user_facing": profile.user_facing,
        "default_suffix": profile.system_prompt_suffix,
        "override_suffix": override,
        "effective_suffix": override if override is not None else profile.system_prompt_suffix,
        "is_default": override is None,
    }
