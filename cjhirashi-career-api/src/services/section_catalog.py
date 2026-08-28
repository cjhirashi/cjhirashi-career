"""Catálogo efectivo de la jerarquía de secciones del Admin (ADR-022).

Lee las 6 tablas reales (``admin_section_groups``, ``admin_sections_l1/l2/l3``,
``admin_views``) con una caché en memoria que se invalida en cada mutación. La
estructura la mantiene el seeder (``services/admin_sections_seed.py``); aquí solo
se sirve el árbol, se reordena/re-parenta secciones y se editan los 2 campos del
operador de cada vista (``responsible_agent_profile_id`` L2 + ``instructions``).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.admin_section_group import AdminSectionGroup
from models.admin_section_l1 import AdminSectionL1
from models.admin_section_l2 import AdminSectionL2
from models.admin_section_l3 import AdminSectionL3
from models.admin_view import AdminView
from services.bedrock.agent_profiles import (
    AGENT_ORCHESTRATOR,
    AgentProfile,
    canonical_profile_id,
    get_profile,
)

logger = logging.getLogger(__name__)

_LEVEL_MODEL = {1: AdminSectionL1, 2: AdminSectionL2, 3: AdminSectionL3}
_LEVEL_PREFIX = {"s1": 1, "s2": 2, "s3": 3}
_OWNER_COL = {1: "owner_l1_id", 2: "owner_l2_id", 3: "owner_l3_id"}


# ---------------------------------------------------------------------------
# Errores de validación (los formatean los callers: ruta vs tool Bedrock)
# ---------------------------------------------------------------------------


class UnknownProfileError(ValueError):
    def __init__(self, value: str):
        self.value = value
        super().__init__(f"unknown agent profile: {value}")


class ProfileNotLevel2Error(ValueError):
    def __init__(self, value: str, level: int):
        self.value = value
        self.level = level
        super().__init__(f"agent profile {value} is L{level}, expected L2")


class EmptyViewUpdateError(ValueError):
    pass


# ---------------------------------------------------------------------------
# Caché en memoria (single-tenant)
# ---------------------------------------------------------------------------

_CACHE: Optional[Dict[str, Any]] = None


def invalidate_cache() -> None:
    global _CACHE
    _CACHE = None


def _level_of(sid: str) -> int:
    prefix = sid.split("-", 1)[0]
    if prefix not in _LEVEL_PREFIX:
        raise KeyError(f"unknown section id: {sid!r}. Usa s1-N | s2-N | s3-N.")
    return _LEVEL_PREFIX[prefix]


# ---------------------------------------------------------------------------
# Serialización
# ---------------------------------------------------------------------------


def _view_public(view: AdminView) -> Dict[str, Any]:
    responsible = view.responsible_agent_profile_id or None
    return {
        "id": view.id,
        "key": view.key,
        "label": view.label,
        "sort_order": view.sort_order,
        "data_source": view.data_source,
        "resource_key": view.resource_key,
        "has_controls_window": bool(view.has_controls_window),
        "tool_names": list(view.tool_names or []),
        "responsible_agent_profile_id": responsible,
        "has_instructions": bool((view.instructions or "").strip()),
        "chat_enabled": responsible is not None,
    }


def _profile_meta(profile_id: Optional[str]) -> Dict[str, Any]:
    if not profile_id:
        return {"label": None, "is_l2": False}
    try:
        prof = get_profile(profile_id)
    except KeyError:
        return {"label": None, "is_l2": False}
    return {"label": prof.label, "is_l2": prof.level == 2}


def _view_item(view: AdminView, section: Any, level: int) -> Dict[str, Any]:
    meta = _profile_meta(view.responsible_agent_profile_id)
    instructions = view.instructions or None
    return {
        "id": view.id,
        "owner": {
            "level": level,
            "section_id": section.id,
            "section_system_name": section.system_name,
            "section_label": section.label,
            "section_path": section.path,
        },
        "key": view.key,
        "label": view.label,
        "sort_order": view.sort_order,
        "data_source": view.data_source,
        "resource_key": view.resource_key,
        "has_controls_window": bool(view.has_controls_window),
        "tool_names": list(view.tool_names or []),
        "responsible_agent_profile_id": view.responsible_agent_profile_id or None,
        "responsible_agent_label": meta["label"],
        "responsible_is_l2": meta["is_l2"],
        "instructions": instructions,
        "chat_enabled": bool(view.responsible_agent_profile_id),
        "instructions_enabled": bool((view.instructions or "").strip()),
    }


# ---------------------------------------------------------------------------
# Carga completa + caché
# ---------------------------------------------------------------------------


async def _load(db: AsyncSession) -> Dict[str, Any]:
    global _CACHE
    if _CACHE is not None:
        return _CACHE

    groups = list((await db.execute(select(AdminSectionGroup))).scalars())
    l1 = list((await db.execute(select(AdminSectionL1))).scalars())
    l2 = list((await db.execute(select(AdminSectionL2))).scalars())
    l3 = list((await db.execute(select(AdminSectionL3))).scalars())
    views = list((await db.execute(select(AdminView))).scalars())

    views_by_owner: Dict[str, List[AdminView]] = {}
    for view in views:
        owner = view.owner_l1_id or view.owner_l2_id or view.owner_l3_id
        views_by_owner.setdefault(owner, []).append(view)
    for bucket in views_by_owner.values():
        bucket.sort(key=lambda v: (v.sort_order, v.key))

    l2_by_parent: Dict[str, List[AdminSectionL2]] = {}
    for row in l2:
        l2_by_parent.setdefault(row.parent_l1_id, []).append(row)
    l3_by_parent: Dict[str, List[AdminSectionL3]] = {}
    for row in l3:
        l3_by_parent.setdefault(row.parent_l2_id, []).append(row)
    l1_by_group: Dict[str, List[AdminSectionL1]] = {}
    for row in l1:
        l1_by_group.setdefault(row.group_id, []).append(row)

    sections_by_id: Dict[str, Any] = {}
    levels: Dict[str, int] = {}
    for row in l1:
        sections_by_id[row.id] = row
        levels[row.id] = 1
    for row in l2:
        sections_by_id[row.id] = row
        levels[row.id] = 2
    for row in l3:
        sections_by_id[row.id] = row
        levels[row.id] = 3

    def _section_node(row: Any, level: int, children: List[Dict[str, Any]]) -> Dict[str, Any]:
        vs = views_by_owner.get(row.id, [])
        return {
            "id": row.id,
            "level": level,
            "system_name": row.system_name,
            "label": row.label,
            "path": row.path,
            "section_type": row.section_type,
            "sort_order": row.sort_order,
            "origin": row.origin,
            "has_layout": len(vs) >= 1,
            "view_count": len(vs),
            "views": [_view_public(v) for v in vs],
            "children": children,
        }

    def _build_l3(parent_l2_id: str) -> List[Dict[str, Any]]:
        rows = sorted(
            l3_by_parent.get(parent_l2_id, []), key=lambda r: (r.sort_order, r.label)
        )
        return [_section_node(r, 3, []) for r in rows]

    def _build_l2(parent_l1_id: str) -> List[Dict[str, Any]]:
        rows = sorted(
            l2_by_parent.get(parent_l1_id, []), key=lambda r: (r.sort_order, r.label)
        )
        return [_section_node(r, 2, _build_l3(r.id)) for r in rows]

    groups_out: List[Dict[str, Any]] = []
    for grp in sorted(groups, key=lambda g: (g.sort_order, g.name)):
        l1_rows = sorted(
            l1_by_group.get(grp.id, []), key=lambda r: (r.sort_order, r.label)
        )
        groups_out.append(
            {
                "id": grp.id,
                "system_name": grp.system_name,
                "name": grp.name,
                "sort_order": grp.sort_order,
                "sections": [
                    _section_node(r, 1, _build_l2(r.id)) for r in l1_rows
                ],
            }
        )

    path_index: Dict[str, tuple] = {}
    for sid, row in sections_by_id.items():
        if row.path:
            path_index[row.path] = (levels[sid], sid)

    _CACHE = {
        "groups": groups_out,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sections_by_id": sections_by_id,
        "levels": levels,
        "views_by_owner": views_by_owner,
        "path_index": path_index,
    }
    return _CACHE


# ---------------------------------------------------------------------------
# nav-tree
# ---------------------------------------------------------------------------


async def list_nav_tree(db: AsyncSession) -> Dict[str, Any]:
    data = await _load(db)
    return {"groups": data["groups"], "generated_at": data["generated_at"]}


# ---------------------------------------------------------------------------
# Grupos
# ---------------------------------------------------------------------------


async def list_section_groups(db: AsyncSession) -> List[Dict[str, Any]]:
    rows = (await db.execute(select(AdminSectionGroup))).scalars()
    return [
        {
            "id": g.id,
            "system_name": g.system_name,
            "name": g.name,
            "sort_order": g.sort_order,
        }
        for g in sorted(rows, key=lambda g: (g.sort_order, g.name))
    ]


async def reorder_groups(db: AsyncSession, order: Sequence[str]) -> List[Dict[str, Any]]:
    rows = {g.id: g for g in (await db.execute(select(AdminSectionGroup))).scalars()}
    if set(order) != set(rows) or len(order) != len(rows):
        raise KeyError("order debe contener exactamente todos los grupos existentes")
    for idx, gid in enumerate(order):
        rows[gid].sort_order = idx * 10
    await db.flush()
    await db.commit()
    invalidate_cache()
    return await list_section_groups(db)


async def update_group(db: AsyncSession, grp_id: str, sort_order: int) -> Dict[str, Any]:
    row = (
        await db.execute(select(AdminSectionGroup).where(AdminSectionGroup.id == grp_id))
    ).scalar_one_or_none()
    if row is None:
        raise KeyError(f"unknown section group: {grp_id}")
    row.sort_order = int(sort_order)
    await db.flush()
    await db.commit()
    invalidate_cache()
    return {
        "id": row.id,
        "system_name": row.system_name,
        "name": row.name,
        "sort_order": row.sort_order,
    }


# ---------------------------------------------------------------------------
# Secciones
# ---------------------------------------------------------------------------


def _section_summary(row: Any, level: int, views: Sequence[AdminView]) -> Dict[str, Any]:
    parent_id = None
    group_id = None
    if level == 1:
        group_id = row.group_id
    elif level == 2:
        parent_id = row.parent_l1_id
    else:
        parent_id = row.parent_l2_id
    return {
        "id": row.id,
        "level": level,
        "system_name": row.system_name,
        "label": row.label,
        "path": row.path,
        "section_type": row.section_type,
        "sort_order": row.sort_order,
        "origin": row.origin,
        "group_id": group_id,
        "parent_id": parent_id,
        "view_count": len(views),
    }


async def list_sections(db: AsyncSession, level: int) -> List[Dict[str, Any]]:
    data = await _load(db)
    rows = [r for sid, r in data["sections_by_id"].items() if data["levels"][sid] == level]
    rows.sort(key=lambda r: (r.sort_order, r.label))
    return [
        _section_summary(r, level, data["views_by_owner"].get(r.id, [])) for r in rows
    ]


async def get_section(db: AsyncSession, sid: str) -> Dict[str, Any]:
    level = _level_of(sid)
    data = await _load(db)
    row = data["sections_by_id"].get(sid)
    if row is None or data["levels"][sid] != level:
        raise KeyError(f"unknown admin section: {sid}")
    views = data["views_by_owner"].get(sid, [])
    summary = _section_summary(row, level, views)
    summary["views"] = [_view_public(v) for v in views]
    return summary


async def update_section(
    db: AsyncSession,
    sid: str,
    *,
    sort_order: Optional[int] = None,
    group_id: Optional[str] = None,
    parent_id: Optional[str] = None,
) -> Dict[str, Any]:
    level = _level_of(sid)
    model = _LEVEL_MODEL[level]
    row = (await db.execute(select(model).where(model.id == sid))).scalar_one_or_none()
    if row is None:
        raise KeyError(f"unknown admin section: {sid}")

    if group_id is not None:
        if level != 1:
            raise ValueError("group_id solo aplica a secciones L1")
        target = (
            await db.execute(
                select(AdminSectionGroup).where(AdminSectionGroup.id == group_id)
            )
        ).scalar_one_or_none()
        if target is None:
            raise ValueError(f"unknown section group: {group_id}")
        row.group_id = group_id

    if parent_id is not None:
        if level == 1:
            raise ValueError("parent_id no aplica a secciones L1 (usa group_id)")
        parent_level = _level_of(parent_id)
        if parent_level != level - 1:
            raise ValueError(
                f"parent_id debe ser una sección L{level - 1} (recibido {parent_id})"
            )
        parent_model = _LEVEL_MODEL[parent_level]
        parent = (
            await db.execute(select(parent_model).where(parent_model.id == parent_id))
        ).scalar_one_or_none()
        if parent is None:
            raise ValueError(f"unknown parent section: {parent_id}")
        if parent_id == sid:
            raise _CycleError("una sección no puede ser su propio padre")
        if level == 2:
            row.parent_l1_id = parent_id
        else:
            row.parent_l2_id = parent_id

    if sort_order is not None:
        row.sort_order = int(sort_order)

    await db.flush()
    await db.commit()
    invalidate_cache()
    return await get_section(db, sid)


class _CycleError(ValueError):
    pass


CycleError = _CycleError


async def reorder_sections(
    db: AsyncSession, container_id: str, order: Sequence[str]
) -> List[Dict[str, Any]]:
    prefix = container_id.split("-", 1)[0]
    if prefix == "grp":
        model, filter_col = AdminSectionL1, AdminSectionL1.group_id
    elif prefix == "s1":
        model, filter_col = AdminSectionL2, AdminSectionL2.parent_l1_id
    elif prefix == "s2":
        model, filter_col = AdminSectionL3, AdminSectionL3.parent_l2_id
    else:
        raise KeyError(f"container_id inválido: {container_id}")

    rows = {
        r.id: r
        for r in (await db.execute(select(model).where(filter_col == container_id))).scalars()
    }
    if set(order) != set(rows) or len(order) != len(rows):
        raise KeyError("order debe listar exactamente las secciones hijas del contenedor")
    for idx, sid in enumerate(order):
        rows[sid].sort_order = idx * 10
    await db.flush()
    await db.commit()
    invalidate_cache()
    level = {"grp": 1, "s1": 2, "s2": 3}[prefix]
    return await list_sections(db, level)


# ---------------------------------------------------------------------------
# Vistas
# ---------------------------------------------------------------------------


async def _view_with_section(db: AsyncSession, view_id: str) -> tuple[AdminView, Any, int]:
    view = (
        await db.execute(select(AdminView).where(AdminView.id == view_id))
    ).scalar_one_or_none()
    if view is None:
        raise KeyError(f"unknown admin view: {view_id}")
    if view.owner_l1_id:
        level, model, oid = 1, AdminSectionL1, view.owner_l1_id
    elif view.owner_l2_id:
        level, model, oid = 2, AdminSectionL2, view.owner_l2_id
    else:
        level, model, oid = 3, AdminSectionL3, view.owner_l3_id
    section = (await db.execute(select(model).where(model.id == oid))).scalar_one()
    return view, section, level


async def list_views(
    db: AsyncSession,
    *,
    section_id: Optional[str] = None,
    responsible: Optional[str] = None,
    data_source: Optional[str] = None,
) -> List[Dict[str, Any]]:
    data = await _load(db)
    if section_id is not None and section_id not in data["sections_by_id"]:
        raise KeyError(f"unknown section: {section_id!r}. Usa s1-N | s2-N | s3-N.")
    out: List[Dict[str, Any]] = []
    for sid, views in data["views_by_owner"].items():
        section = data["sections_by_id"].get(sid)
        if section is None:
            continue
        level = data["levels"][sid]
        if section_id is not None and sid != section_id:
            continue
        for view in views:
            if responsible is not None and (view.responsible_agent_profile_id or None) != responsible:
                continue
            if data_source is not None and view.data_source != data_source:
                continue
            out.append(_view_item(view, section, level))
    out.sort(key=lambda v: (v["owner"]["section_id"], v["sort_order"], v["key"]))
    return out


async def get_view(db: AsyncSession, view_id: str) -> Dict[str, Any]:
    view, section, level = await _view_with_section(db, view_id)
    return _view_item(view, section, level)


def resolve_responsible(value: str) -> str:
    """system name o record id → system name canónico de un perfil **L2**. Valida."""
    try:
        prof = get_profile(value)
    except KeyError as exc:
        raise UnknownProfileError(value) from exc
    if prof.level != 2:
        raise ProfileNotLevel2Error(prof.id, prof.level)
    return canonical_profile_id(value)


_UNSET = object()


async def update_view(
    db: AsyncSession,
    view_id: str,
    *,
    responsible: Any = _UNSET,
    instructions: Any = _UNSET,
) -> Dict[str, Any]:
    if responsible is _UNSET and instructions is _UNSET:
        raise EmptyViewUpdateError(
            "update requiere responsible_agent_profile_id y/o instructions"
        )
    view, section, level = await _view_with_section(db, view_id)

    if responsible is not _UNSET:
        value = (responsible or "").strip()
        view.responsible_agent_profile_id = resolve_responsible(value) if value else None

    if instructions is not _UNSET:
        text_value = (instructions or "").strip()
        view.instructions = text_value or None

    await db.flush()
    await db.commit()
    invalidate_cache()
    fresh, section, level = await _view_with_section(db, view_id)
    return _view_item(fresh, section, level)


# ---------------------------------------------------------------------------
# Resolución de perfil para el chat contextual
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ActiveView:
    section_id: str
    section_level: int
    section_path: Optional[str]
    view_id: Optional[str]
    view_key: Optional[str]
    responsible_agent_profile_id: Optional[str]
    instructions: Optional[str]
    has_controls_window: bool


async def match_active_view(
    db: AsyncSession, route: str, view_key: Optional[str] = None
) -> Optional[ActiveView]:
    data = await _load(db)
    if not route:
        return None
    path = route.split("?")[0].rstrip("/") or "/"
    path_index: Dict[str, tuple] = data["path_index"]

    is_detail = False
    hit = path_index.get(path)
    if hit is None:
        candidates = sorted(
            (p for p in path_index if path.startswith(f"{p}/")),
            key=len,
            reverse=True,
        )
        if not candidates:
            return None
        hit = path_index[candidates[0]]
        is_detail = True

    level, section_id = hit
    section = data["sections_by_id"][section_id]
    views: List[AdminView] = data["views_by_owner"].get(section_id, [])
    if not views:
        return ActiveView(
            section_id=section_id,
            section_level=level,
            section_path=section.path,
            view_id=None,
            view_key=None,
            responsible_agent_profile_id=None,
            instructions=None,
            has_controls_window=False,
        )

    chosen: Optional[AdminView] = None
    if view_key:
        chosen = next((v for v in views if v.key == view_key), None)
    if chosen is None and is_detail:
        chosen = next((v for v in views if v.key in ("view", "record")), None)
    if chosen is None:
        chosen = min(views, key=lambda v: (v.sort_order, v.key))

    return ActiveView(
        section_id=section_id,
        section_level=level,
        section_path=section.path,
        view_id=chosen.id,
        view_key=chosen.key,
        responsible_agent_profile_id=chosen.responsible_agent_profile_id or None,
        instructions=chosen.instructions or None,
        has_controls_window=bool(chosen.has_controls_window),
    )


async def resolve_profile_for_turn(
    db: AsyncSession,
    *,
    chat_surface: str,
    agent_profile_id: Optional[str],
    page_context: Optional[dict],
) -> AgentProfile:
    """Ruta → sección → vista activa → agente L2 responsable. Fallback: orquestador."""
    if chat_surface == "general":
        return get_profile(AGENT_ORCHESTRATOR)
    if agent_profile_id:
        return get_profile(agent_profile_id)

    ctx = page_context or {}
    active = await match_active_view(db, ctx.get("route") or "", ctx.get("view_key"))
    if active and active.responsible_agent_profile_id:
        try:
            prof = get_profile(active.responsible_agent_profile_id)
        except KeyError:
            logger.warning(
                "vista %s: responsable %r desconocido; degradando a orquestador",
                active.view_id,
                active.responsible_agent_profile_id,
            )
        else:
            if prof.level == 2:
                return prof
            logger.warning(
                "vista %s: responsable %s ya no es L2 (L%s); degradando a orquestador",
                active.view_id,
                prof.id,
                prof.level,
            )
    return get_profile(AGENT_ORCHESTRATOR)
