"""Catálogo de agentes — definición de código + estado editable (Admin)."""
from typing import Any, Dict, List, Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.agent_system_conversations import AgentSystemConversation
from services import profile_delegation, profile_prompts, tools as bedrock_tools
from services.agent_profiles import (
    AgentProfile,
    agent_record_id,
    get_profile,
    list_profiles,
    tools_for_profile,
)
from services.methodology_scope import is_shared_methodology
from services.section_catalog import list_views as list_admin_views


def resolved_tool_names(profile: AgentProfile) -> List[str]:
    return sorted(tools_for_profile(profile, bedrock_tools.all_tool_names()))


def _resource_keys(profile: AgentProfile) -> Optional[List[str]]:
    if profile.resource_keys is None:
        return None
    return list(profile.resource_keys)


def _methodology_entries(rows: Sequence[Any], profile_id: str) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for row in rows:
        shared = is_shared_methodology(row.agent_profile_ids)
        ids = row.agent_profile_ids or []
        assigned = shared or (isinstance(ids, list) and profile_id in ids)
        items.append(
            {
                "id": row.id,
                "title": row.title,
                "section": row.section,
                "shared": shared,
                "assigned": assigned,
            }
        )
    return items


def _serialize_definition(profile: AgentProfile, prompt_meta: dict, photo_url: Optional[str] = None) -> Dict[str, Any]:
    return {
        "id": agent_record_id(profile.id),
        "system_name": profile.id,
        "profile_id": profile.id,
        "label": profile.label,
        "level": profile.level,
        "user_facing": profile.user_facing,
        "can_delegate": profile.can_delegate,
        "write_enabled": profile.write_enabled,
        "domain_keys": list(profile.domain_keys),
        "resource_keys": _resource_keys(profile),
        "views": [],
        "default_model_id": profile.default_model_id,
        "tools": resolved_tool_names(profile),
        "has_own_memory": profile.user_facing,
        "default_suffix": prompt_meta["default_suffix"],
        "override_suffix": prompt_meta["override_suffix"],
        "effective_suffix": prompt_meta["effective_suffix"],
        "prompt_is_default": prompt_meta["is_default"],
        "photo_url": photo_url,
    }


async def _conversation_counts(db: AsyncSession, user_id: str) -> Dict[str, int]:
    result = await db.execute(
        select(AgentSystemConversation.agent_profile_id, func.count())
        .where(AgentSystemConversation.user_id == user_id)
        .group_by(AgentSystemConversation.agent_profile_id)
    )
    counts: Dict[str, int] = {}
    for profile_id, total in result.all():
        if profile_id:
            counts[profile_id] = int(total)
    return counts


async def _methodology_rows(db: AsyncSession, user_id: str) -> Sequence[Any]:
    from models.operational_methodology import OperationalMethodology

    result = await db.execute(
        select(OperationalMethodology)
        .where(OperationalMethodology.user_id == user_id)
        .order_by(OperationalMethodology.title.asc())
    )
    return result.scalars().all()


def _with_methodologies(
    item: Dict[str, Any],
    entries: List[Dict[str, Any]],
    *,
    include_all: bool,
) -> Dict[str, Any]:
    assigned = [row for row in entries if row["assigned"]]
    item["methodology_count"] = len(assigned)
    item["assigned_methodologies"] = assigned
    if include_all:
        item["methodologies"] = entries
    return item


def _attach_views(item: Dict[str, Any], owned_views: List[Dict[str, Any]]) -> None:
    """Vistas del Admin que este perfil L2 gestiona (derivado, solo-lectura — ADR-022)."""
    item["views"] = [
        {
            "id": row["id"],  # PK vw-N
            "key": row["key"],
            "label": row["label"],
            "section_id": row["owner"]["section_id"],
            "section_system_name": row["owner"]["section_system_name"],
            "section_path": row["owner"]["section_path"],
            "data_source": row["data_source"],
            "resource_key": row.get("resource_key"),
        }
        for row in owned_views
    ]
    item["resource_keys"] = [
        row["resource_key"] for row in owned_views if row.get("resource_key")
    ] or item.get("resource_keys")


def _attach_delegation(item: Dict[str, Any], state: dict) -> None:
    item["default_delegation_target_ids"] = list(state["default_ids"])
    item["delegation_target_ids"] = list(state["effective_ids"])
    item["allowed_delegation_ids"] = list(state["default_ids"])
    item["delegation_is_default"] = bool(state["is_default"])
    item["delegation_targets"] = profile_delegation.serialize_targets(state["effective_ids"])


async def list_catalog(db: AsyncSession, user_id: str) -> List[Dict[str, Any]]:
    from services import profile_photos

    prompts = {item["profile_id"]: item for item in await profile_prompts.list_profile_prompts(db)}
    photos = await profile_photos.photos_map(db)
    conv_counts = await _conversation_counts(db, user_id)
    rows = await _methodology_rows(db, user_id)
    delegation = await profile_delegation.list_delegation_state(db)
    owned_views_by_agent: Dict[str, List[Dict[str, Any]]] = {}
    for row in await list_admin_views(db):
        owner = row.get("responsible_agent_profile_id")
        if owner:
            owned_views_by_agent.setdefault(owner, []).append(row)
    items: List[Dict[str, Any]] = []
    for profile in list_profiles():
        item = _serialize_definition(profile, prompts[profile.id], photos.get(profile.id))
        item["conversation_count"] = conv_counts.get(profile.id, 0)
        _attach_views(item, owned_views_by_agent.get(profile.id, []))
        _attach_delegation(item, delegation[profile.id])
        items.append(_with_methodologies(item, _methodology_entries(rows, profile.id), include_all=False))
    return items


async def get_catalog_item(
    db: AsyncSession,
    user_id: str,
    profile_id: str,
) -> Dict[str, Any]:
    profile = get_profile(profile_id)
    from services import profile_photos

    prompt_meta = next(
        item for item in await profile_prompts.list_profile_prompts(db) if item["profile_id"] == profile.id
    )
    photos = await profile_photos.photos_map(db)
    rows = await _methodology_rows(db, user_id)
    conv_counts = await _conversation_counts(db, user_id)
    delegation = await profile_delegation.list_delegation_state(db)
    item = _serialize_definition(profile, prompt_meta, photos.get(profile.id))
    item["conversation_count"] = conv_counts.get(profile.id, 0)
    owned_views = [
        row
        for row in await list_admin_views(db)
        if row.get("responsible_agent_profile_id") == profile.id
    ]
    _attach_views(item, owned_views)
    _attach_delegation(item, delegation[profile.id])
    return _with_methodologies(item, _methodology_entries(rows, profile.id), include_all=True)
