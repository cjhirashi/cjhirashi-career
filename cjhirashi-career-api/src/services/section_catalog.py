"""Catálogo efectivo de secciones Admin: código + overrides PG."""
from typing import Any, Dict, List, Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.admin_section_override import AdminSectionOverride
from services.admin_sections import (
    AdminSectionSpec,
    AdminViewSpec,
    get_section_spec,
    is_l2,
    known_section_ids,
    list_section_specs,
    match_section,
)
from services.bedrock.agent_profiles import AgentProfile, get_profile

_ORCHESTRATOR = "agent_orchestrator"


def _view_override(raw: Optional[dict], view: AdminViewSpec) -> Dict[str, Any]:
    """Vista efectiva = registro de código + override PG (feature 001).

    ``sidebar_title`` y ``sidebar_body`` tienen 3 estados por sub-campo:
    - clave ausente en el override → se hereda el texto de código;
    - clave con contenido → override de texto;
    - clave con ``""`` → override vacío explícito (para ``sidebar_body``, oculta
      la pestaña de instrucciones del sidebar).
    Un override cuyo valor coincide con el de código se trata como herencia.
    """
    data = raw.get(view.key) if isinstance(raw, dict) else None
    data = data if isinstance(data, dict) else {}

    def _override(key: str) -> Optional[str]:
        val = data.get(key)
        return val if isinstance(val, str) else None

    desc_ov = _override("description")
    title_ov = _override("sidebar_title")
    body_ov = _override("sidebar_body")

    desc_differs = bool(desc_ov and desc_ov.strip()) and desc_ov.strip() != view.description
    title_differs = title_ov is not None and title_ov != view.sidebar_title
    body_differs = body_ov is not None and body_ov != view.sidebar_body

    return {
        "key": view.key,
        "label": view.label,
        "description": desc_ov.strip() if desc_differs else view.description,
        "sidebar_title": title_ov if title_ov is not None else view.sidebar_title,
        "sidebar_body": body_ov if body_ov is not None else view.sidebar_body,
        "is_default": not (desc_differs or title_differs or body_differs),
    }


def _serialize(spec: AdminSectionSpec, row: Optional[AdminSectionOverride]) -> Dict[str, Any]:
    agent_id = spec.default_agent_profile_id
    agent_is_default = True
    views_raw = None
    if row:
        if row.agent_profile_id is not None:
            agent_id = row.agent_profile_id or None
            agent_is_default = False
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
        "agent_profile_id": agent_id,  # L2 del chat contextual, o None = sin chat
        "agent_label": agent_label,
        "agent_is_default": agent_is_default,
        # Visibilidad del sidebar derecho (feature 001).
        "sidebar_has_chat": agent_id is not None,
        "sidebar_has_instructions": any((v["sidebar_body"] or "").strip() for v in views),
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
    # Un override vacío explícito ({"main": {"sidebar_body": ""}}) NO es vacío:
    # lleva intención del operador (ocultar la pestaña) — la fila se conserva.
    return row.agent_profile_id is None and not views


async def update_section(
    db: AsyncSession,
    section_id: str,
    *,
    agent_profile_id: Optional[str] = None,
    clear_agent: bool = False,
    views: Optional[Dict[str, Dict[str, str]]] = None,
) -> Dict[str, Any]:
    spec = get_section_spec(section_id)
    if agent_profile_id:
        get_profile(agent_profile_id)  # KeyError → 400 "Unknown agent profile"
        if not is_l2(agent_profile_id):
            raise ValueError(f"Agent profile is not L2: {agent_profile_id}")
    row = await _get_or_create_row(db, section_id)
    if clear_agent:
        row.agent_profile_id = None
    elif agent_profile_id is not None:
        row.agent_profile_id = agent_profile_id
    if views is not None:
        cleaned: Dict[str, Dict[str, str]] = {}
        view_specs = {v.key: v for v in spec.views}
        for key, payload in views.items():
            vspec = view_specs.get(key)
            if vspec is None or not isinstance(payload, dict):
                continue  # RF-017: clave de vista desconocida se ignora
            entry: Dict[str, str] = {}
            for field, code_val in (
                ("description", vspec.description),
                ("sidebar_title", vspec.sidebar_title),
                ("sidebar_body", vspec.sidebar_body),
            ):
                if field not in payload or not isinstance(payload[field], str):
                    continue  # RF-007b: sub-campo ausente → se hereda de código
                val = payload[field]
                if field == "description":
                    val = val.strip()
                    if not val or val == code_val.strip():
                        continue
                elif val == code_val:
                    continue  # no-op: igual al código, no se persiste
                # sidebar_title/sidebar_body: "" persiste (override vacío explícito)
                entry[field] = val
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
    if not is_l2(profile_id):
        # feature 001: el agente de una sección (su chat contextual) es L2-only.
        raise ValueError(f"Agent profile is not L2: {profile_id}")
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
    """Perfil del turno de chat (feature 001).

    - ``general`` → orquestador L1.
    - ``contextual`` → override explícito de la request si viene; si no, el
      ``agent_profile_id`` (L2) de la sección de la ruta; si la sección no tiene
      agente o la ruta no hace match con ninguna sección → orquestador L1.
    Nunca lanza por "sección sin agente": degrada al orquestador.
    """
    if chat_surface == "general":
        return get_profile(_ORCHESTRATOR)
    if agent_profile_id:
        return get_profile(agent_profile_id)
    route = (page_context or {}).get("route") or ""
    matched = match_section(route)
    if matched:
        spec, _view_key = matched
        item = await get_section(db, spec.id)
        pid = item.get("agent_profile_id")
        if pid:
            return get_profile(pid)
    return get_profile(_ORCHESTRATOR)
