"""Destinos de delegación efectivos (código por nivel ∩ override Admin)."""
from typing import Dict, List, Optional, Sequence, Set

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.bedrock_agent_delegation import BedrockAgentDelegation
from services.bedrock.agent_profiles import (
    AgentProfile,
    can_delegate_to,
    delegation_targets,
    get_profile,
    list_profiles,
)


def default_delegation_ids(profile: AgentProfile) -> List[str]:
    return [p.id for p in delegation_targets(profile)]


def filter_level_allowed(profile: AgentProfile, target_ids: Sequence[str]) -> List[str]:
    allowed: List[str] = []
    seen: Set[str] = set()
    for tid in target_ids:
        if tid in seen:
            continue
        try:
            target = get_profile(tid)
        except KeyError:
            continue
        if can_delegate_to(profile, target):
            allowed.append(tid)
            seen.add(tid)
    return allowed


async def _overrides_map(db: AsyncSession) -> Dict[str, List[str]]:
    result = await db.execute(select(BedrockAgentDelegation))
    out: Dict[str, List[str]] = {}
    for row in result.scalars().all():
        ids = row.target_ids if isinstance(row.target_ids, list) else []
        out[row.profile_id] = [str(x) for x in ids]
    return out


async def get_effective_delegation_ids(db: AsyncSession, profile: AgentProfile) -> List[str]:
    defaults = default_delegation_ids(profile)
    overrides = await _overrides_map(db)
    if profile.id not in overrides:
        return defaults
    return filter_level_allowed(profile, overrides[profile.id])


async def list_delegation_state(db: AsyncSession) -> Dict[str, dict]:
    overrides = await _overrides_map(db)
    items: Dict[str, dict] = {}
    for profile in list_profiles():
        defaults = default_delegation_ids(profile)
        is_default = profile.id not in overrides
        effective = defaults if is_default else filter_level_allowed(profile, overrides[profile.id])
        items[profile.id] = {
            "default_ids": defaults,
            "effective_ids": effective,
            "is_default": is_default,
        }
    return items


def serialize_targets(ids: Sequence[str]) -> List[dict]:
    items = []
    for tid in ids:
        try:
            p = get_profile(tid)
        except KeyError:
            continue
        items.append({"id": p.id, "label": p.label, "level": p.level})
    return items


async def set_delegation_targets(
    db: AsyncSession,
    profile_id: str,
    target_ids: Optional[Sequence[str]],
) -> dict:
    profile = get_profile(profile_id)
    profile_id = profile.id
    result = await db.execute(
        select(BedrockAgentDelegation).where(BedrockAgentDelegation.profile_id == profile_id)
    )
    row = result.scalar_one_or_none()
    if target_ids is None:
        if row:
            await db.delete(row)
            await db.commit()
    else:
        filtered = filter_level_allowed(profile, target_ids)
        if row:
            row.target_ids = filtered
        else:
            db.add(BedrockAgentDelegation(profile_id=profile_id, target_ids=filtered))
        await db.commit()
    effective = await get_effective_delegation_ids(db, profile)
    defaults = default_delegation_ids(profile)
    overrides = await _overrides_map(db)
    return {
        "profile_id": profile.id,
        "default_ids": defaults,
        "effective_ids": effective,
        "is_default": profile.id not in overrides,
        "targets": serialize_targets(effective),
    }
