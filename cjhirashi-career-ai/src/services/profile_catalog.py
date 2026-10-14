"""Catálogo de agentes: definición de código + estado editable (BD propia) + datos de la API por REST.

Traslado de `cjhirashi-career-api/src/services/bedrock/profile_catalog.py`, `methodology_scope.py`
(lectura) y `section_catalog.py` (derivación de tools). Las metodologías (`/career/operational-methodologies`)
y las secciones (`/admin/sections`) se leen con los clientes REST (D-10); aquí viven las reglas
(`applies_to_caller`, tools derivadas por sección) y el cruce con los overrides de `career_ai_db`.
"""
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from clients.sections import MethodologiesClient, SectionsClient
from repositories import conversation_repo, profile_repo
from services import tools_registry
from services.agent_profiles import (
    AGENT_METHODOLOGIES,
    AgentProfile,
    agent_record_id,
    delegation_targets,
    filter_level_allowed,
    get_profile,
    list_profiles,
)

SECTION_TABLE = "table"

# CRUD genérico de las secciones tabla con `resource_key` (spec 004 D-3). Sin `search_knowledge_base` (D-15).
TABLE_SECTION_TOOLS: Tuple[str, ...] = (
    "list_career_record",
    "get_career_record",
    "create_career_record",
    "update_career_record",
    "delete_career_record",
    "bulk_update_career_record",
    "count_career_records",
    "describe_resource_schema",
)


# ---------------------------------------------------------------------------- metodologías

def is_shared_methodology(agent_profile_ids: Optional[Any]) -> bool:
    """True si la metodología aplica a todos los agentes (lista vacía o null)."""
    ids = agent_profile_ids or []
    return not isinstance(ids, list) or not ids


def applies_to_caller(
    agent_profile_ids: Optional[Any],
    section_ids: Optional[Any],
    caller_profile_id: Optional[str],
    caller_section_ids: Optional[Any],
) -> bool:
    """True si la metodología es visible para el caller (spec 004).

    Compartida (ambas listas vacías) -> todos; guardián -> todas; L1/L3 -> su id en
    `agent_profile_ids`; L2 -> alguna de sus secciones en `section_ids`.
    """
    if not caller_profile_id or caller_profile_id == AGENT_METHODOLOGIES:
        return True
    a_ids = agent_profile_ids if isinstance(agent_profile_ids, list) else []
    s_ids = section_ids if isinstance(section_ids, list) else []
    if not a_ids and not s_ids:
        return True
    if caller_profile_id in a_ids:
        return True
    caller_secs = caller_section_ids if isinstance(caller_section_ids, list) else []
    return bool(set(s_ids) & set(caller_secs))


async def list_assigned_methodologies(
    methodologies: MethodologiesClient,
    caller_profile_id: str,
    caller_section_ids: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Metodologías que el caller debe consultar (orden por título), con su procedencia por sección."""
    rows = sorted(await methodologies.list(), key=lambda r: r.get("title") or "")
    assigned: List[Dict[str, Any]] = []
    for row in rows:
        if not applies_to_caller(
            row.get("agent_profile_ids"), row.get("section_ids"), caller_profile_id, caller_section_ids
        ):
            continue
        a_ids = row.get("agent_profile_ids") if isinstance(row.get("agent_profile_ids"), list) else []
        s_ids = row.get("section_ids") if isinstance(row.get("section_ids"), list) else []
        assigned.append(
            {"id": row["id"], "title": row.get("title"), "section_ids": s_ids, "shared": not a_ids and not s_ids}
        )
    return assigned


def _methodology_entries(rows: Sequence[Dict[str, Any]], profile_id: str) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for row in sorted(rows, key=lambda r: r.get("title") or ""):
        shared = is_shared_methodology(row.get("agent_profile_ids"))
        ids = row.get("agent_profile_ids") or []
        assigned = shared or (isinstance(ids, list) and profile_id in ids)
        items.append({"id": row["id"], "title": row.get("title"), "shared": shared, "assigned": assigned})
    return items


# ---------------------------------------------------------------------------- tools por sección

def section_tools(section: Dict[str, Any]) -> Set[str]:
    """Herramientas que controla una sección (spec 004 RF-001), derivadas de su fila de `/admin/sections`."""
    names = set(section.get("related_tools") or [])
    if section.get("section_type") == SECTION_TABLE and section.get("resource_key"):
        names |= set(TABLE_SECTION_TOOLS)
    names.discard("search_knowledge_base")
    return names


def _owned_sections(sections: Sequence[Dict[str, Any]], profile_id: str) -> List[Dict[str, Any]]:
    return [s for s in sections if s.get("agent_profile_id") == profile_id]


async def derived_tools_for_agent(sections: SectionsClient, profile_id: str) -> Set[str]:
    """Unión de las tools de TODAS las secciones que el agente L2 posee."""
    tools: Set[str] = set()
    for item in _owned_sections(await sections.list(), profile_id):
        tools |= section_tools(item)
    return tools


async def resolve_effective_tools(
    db: AsyncSession, sections: SectionsClient, profile: AgentProfile
) -> Tuple[Set[str], List[str]]:
    """Set efectivo de tools y ids de sección del caller, resuelto una vez por turno (spec 004 RF-002)."""
    if profile.level == 2:
        owned = _owned_sections(await sections.list(), profile.id)
        union: Set[str] = set()
        for item in owned:
            union |= section_tools(item)
        return tools_registry.effective_tool_names(profile, None, section_tools=union), [s["id"] for s in owned]
    override = await profile_repo.get_tool_override(db, profile.id)
    return tools_registry.effective_tool_names(profile, override), []


# ---------------------------------------------------------------------------- delegación

def default_delegation_ids(profile: AgentProfile) -> List[str]:
    return [p.id for p in delegation_targets(profile)]


def serialize_targets(ids: Sequence[str]) -> List[dict]:
    items = []
    for tid in ids:
        try:
            p = get_profile(tid)
        except KeyError:
            continue
        items.append({"id": p.id, "label": p.label, "level": p.level})
    return items


def _delegation_state(profile: AgentProfile, overrides: Dict[str, List[str]]) -> dict:
    defaults = default_delegation_ids(profile)
    is_default = profile.id not in overrides
    effective = defaults if is_default else filter_level_allowed(profile, overrides[profile.id])
    return {"default_ids": defaults, "effective_ids": effective, "is_default": is_default}


# ---------------------------------------------------------------------------- catálogo

def _prompt_meta(profile: AgentProfile, overrides: Dict[str, str]) -> dict:
    override = overrides.get(profile.id)
    return {
        "default_suffix": profile.system_prompt_suffix,
        "override_suffix": override,
        "effective_suffix": override if override is not None else profile.system_prompt_suffix,
        "is_default": override is None,
    }


def _serialize_definition(
    profile: AgentProfile,
    prompt_meta: dict,
    photo_url: Optional[str],
    tool_override: Optional[List[str]],
) -> Dict[str, Any]:
    effective = sorted(tools_registry.effective_tool_names(profile, tool_override))
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
        "resource_keys": list(profile.resource_keys) if profile.resource_keys is not None else None,
        "sections": [],
        "default_model_id": profile.default_model_id,
        "tools": effective,
        "default_tools": sorted(tools_registry.default_tool_names(profile)),
        "override_tools": sorted(tool_override) if tool_override is not None else None,
        "effective_tools": effective,
        "has_own_memory": profile.user_facing,
        "default_suffix": prompt_meta["default_suffix"],
        "override_suffix": prompt_meta["override_suffix"],
        "effective_suffix": prompt_meta["effective_suffix"],
        "prompt_is_default": prompt_meta["is_default"],
        "photo_url": photo_url,
    }


def _attach_sections(item: Dict[str, Any], owned: List[Dict[str, Any]]) -> None:
    item["sections"] = [
        {k: row.get(k) for k in ("id", "system_name", "label", "section_type", "path")} for row in owned
    ]
    item["resource_keys"] = [r["resource_key"] for r in owned if r.get("resource_key")] or item.get("resource_keys")


def _attach_delegation(item: Dict[str, Any], state: dict) -> None:
    item["default_delegation_target_ids"] = list(state["default_ids"])
    item["delegation_target_ids"] = list(state["effective_ids"])
    item["allowed_delegation_ids"] = list(state["default_ids"])
    item["delegation_is_default"] = bool(state["is_default"])
    item["delegation_targets"] = serialize_targets(state["effective_ids"])


def _with_methodologies(item: Dict[str, Any], entries: List[Dict[str, Any]], *, include_all: bool) -> Dict[str, Any]:
    assigned = [row for row in entries if row["assigned"]]
    item["methodology_count"] = len(assigned)
    item["assigned_methodologies"] = assigned
    if include_all:
        item["methodologies"] = entries
    return item


async def list_catalog(
    db: AsyncSession,
    user_id: str,
    *,
    sections: SectionsClient,
    methodologies: MethodologiesClient,
) -> List[Dict[str, Any]]:
    prompts = await profile_repo.list_prompt_overrides(db)
    photos = await profile_repo.photos_map(db)
    tool_overrides = await profile_repo.list_tool_overrides(db)
    delegation_overrides = await profile_repo.list_delegation_overrides(db)
    counts = await conversation_repo.conversation_counts_by_profile(db, user_id)
    meth_rows = await methodologies.list()
    section_rows = await sections.list()
    items: List[Dict[str, Any]] = []
    for profile in list_profiles():
        item = _serialize_definition(
            profile, _prompt_meta(profile, prompts), photos.get(profile.id), tool_overrides.get(profile.id)
        )
        item["conversation_count"] = counts.get(profile.id, 0)
        _attach_sections(item, _owned_sections(section_rows, profile.id))
        _attach_delegation(item, _delegation_state(profile, delegation_overrides))
        items.append(_with_methodologies(item, _methodology_entries(meth_rows, profile.id), include_all=False))
    return items


async def get_catalog_item(
    db: AsyncSession,
    user_id: str,
    profile_id: str,
    *,
    sections: SectionsClient,
    methodologies: MethodologiesClient,
) -> Dict[str, Any]:
    profile = get_profile(profile_id)  # KeyError si no existe
    prompts = await profile_repo.list_prompt_overrides(db)
    photos = await profile_repo.photos_map(db)
    tool_override = await profile_repo.get_tool_override(db, profile.id)
    delegation_overrides = await profile_repo.list_delegation_overrides(db)
    counts = await conversation_repo.conversation_counts_by_profile(db, user_id)
    item = _serialize_definition(profile, _prompt_meta(profile, prompts), photos.get(profile.id), tool_override)
    item["conversation_count"] = counts.get(profile.id, 0)
    _attach_sections(item, _owned_sections(await sections.list(), profile.id))
    _attach_delegation(item, _delegation_state(profile, delegation_overrides))
    return _with_methodologies(
        item, _methodology_entries(await methodologies.list(), profile.id), include_all=True
    )
