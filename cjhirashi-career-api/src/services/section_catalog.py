"""Catálogo efectivo de secciones Admin: código + overrides PG."""
from typing import Any, Dict, List, Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.admin_section_override import AdminSectionOverride
from services.admin_sections import (
    AdminSectionSpec,
    AdminViewSpec,
    chat_agent_id,
    get_section_spec,
    known_section_ids,
    list_section_specs,
    match_section,
)
from services.bedrock.agent_profiles import (
    AgentProfile,
    get_profile,
    resolve_agent_profile,
)


def _view_override(raw: Optional[dict], view: AdminViewSpec) -> Dict[str, str]:
    data = raw.get(view.key) if isinstance(raw, dict) else None
    data = data if isinstance(data, dict) else {}
    return {
        "key": view.key,
        "label": view.label,
        "description": (data.get("description") or view.description).strip() or view.description,
        "sidebar_title": (data.get("sidebar_title") or view.sidebar_title).strip()
        or view.sidebar_title,
        "sidebar_body": (data.get("sidebar_body") or view.sidebar_body).strip() or view.sidebar_body,
        "is_default": not bool(
            (data.get("description") or "").strip()
            or (data.get("sidebar_title") or "").strip()
            or (data.get("sidebar_body") or "").strip()
        ),
    }


def _serialize(spec: AdminSectionSpec, row: Optional[AdminSectionOverride]) -> Dict[str, Any]:
    agent_id = spec.default_agent_profile_id
    agent_is_default = True
    description = spec.description
    description_is_default = True
    views_raw = None
    if row:
        if row.agent_profile_id is not None:
            agent_id = row.agent_profile_id or None
            agent_is_default = False
        if row.description is not None and row.description.strip():
            description = row.description.strip()
            description_is_default = False
        views_raw = row.views
    views = [_view_override(views_raw, view) for view in spec.views]
    agent_label = None
    if agent_id:
        try:
            agent_label = get_profile(agent_id).label
        except KeyError:
            agent_label = agent_id
    return {
        "id": spec.id,  # PK sec-N (ADR-021)
        "system_name": spec.system_name,  # slug legible
        "label": spec.label,
        "path": spec.path,
        "section_type": spec.section_type,
        "group": spec.group,
        "resource_key": spec.resource_key,
        "related_tools": list(spec.related_tools),
        "default_agent_profile_id": spec.default_agent_profile_id,
        "agent_profile_id": agent_id,
        "agent_label": agent_label,
        "chat_agent_profile_id": chat_agent_id(agent_id),
        "agent_is_default": agent_is_default,
        "description": description,
        "description_is_default": description_is_default,
        "view_count": len(views),
        "views": views,
    }


async def _overrides_map(db: AsyncSession) -> Dict[str, AdminSectionOverride]:
    result = await db.execute(select(AdminSectionOverride))
    return {row.section_id: row for row in result.scalars().all()}


async def list_sections(db: AsyncSession) -> List[Dict[str, Any]]:
    overrides = await _overrides_map(db)
    return [_serialize(spec, overrides.get(spec.id)) for spec in list_section_specs()]


async def get_section(db: AsyncSession, section_id: str) -> Dict[str, Any]:
    spec = get_section_spec(section_id)
    overrides = await _overrides_map(db)
    return _serialize(spec, overrides.get(section_id))


async def sections_for_agent(db: AsyncSession, profile_id: str) -> List[Dict[str, Any]]:
    return [item for item in await list_sections(db) if item["agent_profile_id"] == profile_id]


async def _get_or_create_row(db: AsyncSession, section_id: str) -> AdminSectionOverride:
    result = await db.execute(
        select(AdminSectionOverride).where(AdminSectionOverride.section_id == section_id)
    )
    row = result.scalar_one_or_none()
    if row:
        return row
    row = AdminSectionOverride(section_id=section_id)
    db.add(row)
    await db.flush()
    return row


def _row_is_empty(row: AdminSectionOverride) -> bool:
    views = row.views if isinstance(row.views, dict) else {}
    return (
        row.agent_profile_id is None
        and not (row.description or "").strip()
        and not views
    )


async def update_section(
    db: AsyncSession,
    section_id: str,
    *,
    agent_profile_id: Optional[str] = None,
    clear_agent: bool = False,
    description: Optional[str] = None,
    clear_description: bool = False,
    views: Optional[Dict[str, Dict[str, str]]] = None,
) -> Dict[str, Any]:
    get_section_spec(section_id)
    if agent_profile_id:
        get_profile(agent_profile_id)
    row = await _get_or_create_row(db, section_id)
    if clear_agent:
        row.agent_profile_id = None
    elif agent_profile_id is not None:
        row.agent_profile_id = agent_profile_id
    if clear_description:
        row.description = None
    elif description is not None:
        row.description = description.strip() or None
    if views is not None:
        cleaned: Dict[str, Dict[str, str]] = {}
        spec = get_section_spec(section_id)
        allowed = {v.key for v in spec.views}
        for key, payload in views.items():
            if key not in allowed or not isinstance(payload, dict):
                continue
            entry = {
                field: (payload.get(field) or "").strip()
                for field in ("description", "sidebar_title", "sidebar_body")
                if (payload.get(field) or "").strip()
            }
            if entry:
                cleaned[key] = entry
        row.views = cleaned or None
    if _row_is_empty(row):
        await db.delete(row)
    await db.commit()
    return await get_section(db, section_id)


async def set_agent_sections(
    db: AsyncSession,
    profile_id: str,
    section_ids: Sequence[str],
) -> List[Dict[str, Any]]:
    profile_id = get_profile(profile_id).id
    wanted = []
    for sid in section_ids:
        if sid not in known_section_ids():
            raise KeyError(f"Unknown admin section: {sid}")
        wanted.append(sid)
    wanted_set = set(wanted)
    current = await list_sections(db)
    owned = {item["id"] for item in current if item["agent_profile_id"] == profile_id}
    for sid in wanted_set:
        spec = get_section_spec(sid)
        if spec.default_agent_profile_id == profile_id:
            row = await _get_or_create_row(db, sid)
            row.agent_profile_id = None
            if _row_is_empty(row):
                await db.delete(row)
        else:
            row = await _get_or_create_row(db, sid)
            row.agent_profile_id = profile_id
    for sid in owned - wanted_set:
        spec = get_section_spec(sid)
        if spec.default_agent_profile_id == profile_id:
            continue
        row = await _get_or_create_row(db, sid)
        row.agent_profile_id = None
        if _row_is_empty(row):
            await db.delete(row)
    await db.commit()
    return await sections_for_agent(db, profile_id)


async def resolve_profile_for_turn(
    db: AsyncSession,
    *,
    chat_surface: str,
    agent_profile_id: Optional[str],
    page_context: Optional[dict],
) -> AgentProfile:
    """Resuelve el perfil de chat usando el catálogo de secciones (con fallback de código)."""
    if chat_surface == "general":
        return get_profile(chat_agent_id(None) or "agent_orchestrator")
    if agent_profile_id:
        return get_profile(agent_profile_id)
    route = (page_context or {}).get("route") or ""
    matched = match_section(route)
    if matched:
        spec, _view_key = matched
        item = await get_section(db, spec.id)
        chat_id = item.get("chat_agent_profile_id")
        if chat_id:
            return get_profile(chat_id)
    return resolve_agent_profile(
        chat_surface=chat_surface,
        agent_profile_id=agent_profile_id,
        page_context=page_context,
    )
