"""Catálogo efectivo de la jerarquía de secciones del Admin (ADR-022; CRUD ADR-023).

Lee las 6 tablas reales (``admin_section_groups``, ``admin_sections_l1/l2/l3``,
``admin_views``) con una caché en memoria que se invalida en cada mutación.
Desde ADR-023 (corrección) el CRUD de grupos y secciones es 100% Admin: crear,
editar, borrar, mover entre niveles. El seeder (``services/admin_sections_seed.py``)
deja de tocar grupos/secciones tras el primer arranque; solo sigue sembrando
vistas y el alta idempotente del grupo/sección protegidos ``admin``.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence

from sqlalchemy import func, select
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
_PARENT_COL = {2: "parent_l1_id", 3: "parent_l2_id"}

# ADR-023 (corrección) §3.1 — enum genérico, extensible sin migrar schema.
# Única fuente de verdad; validado también en schemas/admin_sections.py.
VISIBILITY_LEVELS: tuple[str, ...] = ("standard", "superuser")

# ADR-023 (corrección) §3.2 — system_name reservado del único grupo protegido.
ADMIN_GROUP_SYSTEM_NAME = "admin"
ADMIN_SECTION_SYSTEM_NAME = "admin-sections"


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


class ProtectedResourceError(ValueError):
    """El recurso no forma parte del CRUD genérico (grupo/sección `admin`)."""


class ForbiddenVisibilityError(PermissionError):
    """El usuario actual no satisface el ``visibility_level`` del recurso."""


class HasChildrenError(ValueError):
    """El grupo/sección tiene hijas vivas; borrado/move bloqueado (sin cascada)."""


class HasViewsError(ValueError):
    """La sección tiene vistas propias; borrado bloqueado (sin cascada)."""


class UnknownSectionTargetError(ValueError):
    """``owner_l{n}_id`` de destino (reasignación de vista) no existe."""

    def __init__(self, value: str):
        self.value = value
        super().__init__(f"unknown target section: {value}")


class DuplicateViewKeyError(ValueError):
    """La sección destino ya tiene una vista con el mismo ``key`` (reasignación)."""

    def __init__(self, section_id: str, key: str):
        self.section_id = section_id
        self.key = key
        super().__init__(f"section {section_id} already has a view with key {key!r}")


# Sentinel "campo ausente" (≠ None explícito) — usado por update_section (path)
# y update_view (responsible/instructions/owner_*).
_UNSET = object()


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
        "visibility_level": view.visibility_level,
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
        "visibility_level": view.visibility_level,
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
            "visibility_level": row.visibility_level,
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
                "visibility_level": grp.visibility_level,
                "sections": [
                    _section_node(r, 1, _build_l2(r.id)) for r in l1_rows
                ],
            }
        )

    path_index: Dict[str, tuple] = {}
    for sid, row in sections_by_id.items():
        if row.path:
            path_index[row.path] = (levels[sid], sid)

    groups_by_id: Dict[str, AdminSectionGroup] = {g.id: g for g in groups}

    _CACHE = {
        "groups": groups_out,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "groups_by_id": groups_by_id,
        "sections_by_id": sections_by_id,
        "levels": levels,
        "views_by_owner": views_by_owner,
        "path_index": path_index,
    }
    return _CACHE


# ---------------------------------------------------------------------------
# Gate genérico de visibilidad (ADR-023 corrección §3.3)
# ---------------------------------------------------------------------------


async def _root_group_id_of_section(db: AsyncSession, sid: str) -> str:
    """Sube hasta el grupo raíz de una sección L1/L2/L3, usando la caché."""
    data = await _load(db)
    row = data["sections_by_id"].get(sid)
    if row is None:
        raise KeyError(f"unknown admin section: {sid}")
    level = data["levels"][sid]
    while level != 1:
        parent_id = row.parent_l1_id if level == 2 else row.parent_l2_id
        row = data["sections_by_id"][parent_id]
        level = data["levels"][parent_id]
    return row.group_id


async def _is_admin_subtree(db: AsyncSession, section_or_group_id: str) -> bool:
    """True si el grupo, o el grupo raíz de la sección dada, es el grupo protegido `admin`."""
    data = await _load(db)
    prefix = section_or_group_id.split("-", 1)[0]
    if prefix == "grp":
        group = data["groups_by_id"].get(section_or_group_id)
        if group is None:
            raise KeyError(f"unknown section group: {section_or_group_id}")
        return group.system_name == ADMIN_GROUP_SYSTEM_NAME
    root_group_id = await _root_group_id_of_section(db, section_or_group_id)
    group = data["groups_by_id"].get(root_group_id)
    return group is not None and group.system_name == ADMIN_GROUP_SYSTEM_NAME


def _visibility_satisfied(visibility_level: str, is_superuser: bool) -> bool:
    if visibility_level == "superuser":
        return is_superuser
    return True


async def _require_visibility(db: AsyncSession, *, visibility_level: str, is_superuser: bool) -> None:
    if not _visibility_satisfied(visibility_level, is_superuser):
        raise ForbiddenVisibilityError(
            "forbidden: the admin group is restricted to superusers"
        )


def _filter_groups_for_user(groups: List[Dict[str, Any]], is_superuser: bool) -> List[Dict[str, Any]]:
    if is_superuser:
        return groups
    return [g for g in groups if g["visibility_level"] != "superuser"]


# ---------------------------------------------------------------------------
# nav-tree
# ---------------------------------------------------------------------------


async def list_nav_tree(db: AsyncSession, *, is_superuser: bool = False) -> Dict[str, Any]:
    data = await _load(db)
    groups = _filter_groups_for_user(data["groups"], is_superuser)
    return {"groups": groups, "generated_at": data["generated_at"]}


# ---------------------------------------------------------------------------
# Grupos
# ---------------------------------------------------------------------------


def _group_item(g: AdminSectionGroup) -> Dict[str, Any]:
    return {
        "id": g.id,
        "system_name": g.system_name,
        "name": g.name,
        "sort_order": g.sort_order,
        "origin": g.origin,
        "visibility_level": g.visibility_level,
    }


async def list_section_groups(
    db: AsyncSession, *, is_superuser: bool = False
) -> List[Dict[str, Any]]:
    rows = (await db.execute(select(AdminSectionGroup))).scalars()
    items = [
        _group_item(g) for g in sorted(rows, key=lambda g: (g.sort_order, g.name))
    ]
    if is_superuser:
        return items
    return [i for i in items if i["visibility_level"] != "superuser"]


async def create_group(
    db: AsyncSession,
    *,
    name: str,
    system_name: str,
    sort_order: Optional[int] = None,
    visibility_level: str = "standard",
) -> Dict[str, Any]:
    if visibility_level not in VISIBILITY_LEVELS:
        raise ValueError(f"visibility_level debe ser uno de {VISIBILITY_LEVELS}")
    if system_name == ADMIN_GROUP_SYSTEM_NAME:
        raise ProtectedResourceError(
            "system_name 'admin' is reserved for the protected admin group"
        )

    existing = (
        await db.execute(
            select(AdminSectionGroup).where(
                (AdminSectionGroup.name == name)
                | (AdminSectionGroup.system_name == system_name)
            )
        )
    ).scalars().first()
    if existing is not None:
        raise _DuplicateError(f"group name or system_name already exists: {name!r}/{system_name!r}")

    if sort_order is None:
        max_sort = (
            await db.execute(select(func.max(AdminSectionGroup.sort_order)))
        ).scalar()
        sort_order = (max_sort or 0) + 10

    row = AdminSectionGroup(
        system_name=system_name,
        name=name,
        sort_order=sort_order,
        visibility_level=visibility_level,
    )
    db.add(row)
    await db.flush()
    await db.commit()
    invalidate_cache()
    return _group_item(row)


async def delete_group(db: AsyncSession, grp_id: str, *, is_superuser: bool) -> None:
    row = (
        await db.execute(select(AdminSectionGroup).where(AdminSectionGroup.id == grp_id))
    ).scalar_one_or_none()
    if row is None:
        raise KeyError(f"unknown section group: {grp_id}")
    if row.system_name == ADMIN_GROUP_SYSTEM_NAME:
        raise ProtectedResourceError("the admin group is protected and cannot be deleted")
    await _require_visibility(db, visibility_level=row.visibility_level, is_superuser=is_superuser)

    child_count = (
        await db.execute(
            select(func.count()).select_from(AdminSectionL1).where(
                AdminSectionL1.group_id == grp_id
            )
        )
    ).scalar_one()
    if child_count:
        raise HasChildrenError(
            f"group {grp_id} has {child_count} child section(s); move or delete them first"
        )

    await db.delete(row)
    await db.flush()
    await db.commit()
    invalidate_cache()


async def reorder_groups(db: AsyncSession, order: Sequence[str]) -> List[Dict[str, Any]]:
    rows = {g.id: g for g in (await db.execute(select(AdminSectionGroup))).scalars()}
    if set(order) != set(rows) or len(order) != len(rows):
        raise KeyError("order debe contener exactamente todos los grupos existentes")
    for idx, gid in enumerate(order):
        rows[gid].sort_order = idx * 10
    await db.flush()
    await db.commit()
    invalidate_cache()
    return await list_section_groups(db, is_superuser=True)


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
    return _group_item(row)


# ---------------------------------------------------------------------------
# Secciones
# ---------------------------------------------------------------------------


class _DuplicateError(ValueError):
    pass


DuplicateError = _DuplicateError


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
        "visibility_level": row.visibility_level,
        "group_id": group_id,
        "parent_id": parent_id,
        "view_count": len(views),
    }


async def _filter_sections_for_user(
    db: AsyncSession, rows: List[Any], is_superuser: bool
) -> List[Any]:
    if is_superuser:
        return rows
    out = []
    for row in rows:
        if row.visibility_level == "superuser":
            continue
        if await _is_admin_subtree(db, row.id):
            continue
        out.append(row)
    return out


async def list_sections(
    db: AsyncSession, level: int, *, is_superuser: bool = False
) -> List[Dict[str, Any]]:
    data = await _load(db)
    rows = [r for sid, r in data["sections_by_id"].items() if data["levels"][sid] == level]
    rows.sort(key=lambda r: (r.sort_order, r.label))
    rows = await _filter_sections_for_user(db, rows, is_superuser)
    return [
        _section_summary(r, level, data["views_by_owner"].get(r.id, [])) for r in rows
    ]


async def get_section(
    db: AsyncSession, sid: str, *, is_superuser: bool = False
) -> Dict[str, Any]:
    level = _level_of(sid)
    data = await _load(db)
    row = data["sections_by_id"].get(sid)
    if row is None or data["levels"][sid] != level:
        raise KeyError(f"unknown admin section: {sid}")
    if not is_superuser and (
        row.visibility_level == "superuser" or await _is_admin_subtree(db, sid)
    ):
        # ADR-023 §3.3: 404, no 403 — no confirmar existencia a quien no puede verla.
        raise KeyError(f"unknown admin section: {sid}")
    views = data["views_by_owner"].get(sid, [])
    summary = _section_summary(row, level, views)
    summary["views"] = [_view_public(v) for v in views]
    return summary


async def _is_protected_section(db: AsyncSession, sid: str) -> bool:
    """True si `sid` ES la sección protegida "Secciones del Admin" (§1.4/§1.5/§1.6)."""
    data = await _load(db)
    row = data["sections_by_id"].get(sid)
    if row is None or data["levels"].get(sid) != 1:
        return False
    return row.system_name == ADMIN_SECTION_SYSTEM_NAME


async def create_section(
    db: AsyncSession,
    *,
    level: int,
    label: str,
    system_name: str,
    section_type: str,
    path: Optional[str] = None,
    group_id: Optional[str] = None,
    parent_id: Optional[str] = None,
    visibility_level: str = "standard",
    is_superuser: bool = False,
) -> Dict[str, Any]:
    if visibility_level not in VISIBILITY_LEVELS:
        raise ValueError(f"visibility_level debe ser uno de {VISIBILITY_LEVELS}")
    if level not in (1, 2, 3):
        raise ValueError("level debe ser 1, 2 o 3")

    if level == 1:
        if group_id is None or parent_id is not None:
            raise ValueError("level=1 requiere group_id y no admite parent_id")
        group = (
            await db.execute(select(AdminSectionGroup).where(AdminSectionGroup.id == group_id))
        ).scalar_one_or_none()
        if group is None:
            raise ValueError(f"unknown section group: {group_id}")
        if group.system_name == ADMIN_GROUP_SYSTEM_NAME and not is_superuser:
            raise ForbiddenVisibilityError(
                "forbidden: the admin group is restricted to superusers"
            )
        if group.system_name == ADMIN_GROUP_SYSTEM_NAME:
            raise ProtectedResourceError(
                "cannot create a section inside the protected admin group"
            )
    else:
        if parent_id is None or group_id is not None:
            raise ValueError("level in (2,3) requiere parent_id y no admite group_id")
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
        if await _is_admin_subtree(db, parent_id):
            raise ProtectedResourceError(
                "cannot create a section inside the protected admin group"
            )

    model = _LEVEL_MODEL[level]
    existing_name = (
        await db.execute(select(model).where(model.system_name == system_name))
    ).scalar_one_or_none()
    if existing_name is not None:
        raise _DuplicateError(f"system_name already exists: {system_name!r}")

    if path:
        for lvl, mdl in _LEVEL_MODEL.items():
            clash = (
                await db.execute(select(mdl).where(mdl.path == path))
            ).scalar_one_or_none()
            if clash is not None:
                raise _DuplicateError(f"path already exists: {path!r}")

    kwargs: Dict[str, Any] = dict(
        system_name=system_name,
        label=label,
        path=path,
        section_type=section_type,
        origin="admin",
        visibility_level=visibility_level,
    )
    if level == 1:
        kwargs["group_id"] = group_id
    elif level == 2:
        kwargs["parent_l1_id"] = parent_id
    else:
        kwargs["parent_l2_id"] = parent_id

    row = model(**kwargs)
    db.add(row)
    await db.flush()
    await db.commit()
    invalidate_cache()
    return await get_section(db, row.id, is_superuser=True)


async def update_section(
    db: AsyncSession,
    sid: str,
    *,
    label: Optional[str] = None,
    system_name: Optional[str] = None,
    path: Any = _UNSET,
    section_type: Optional[str] = None,
    sort_order: Optional[int] = None,
    visibility_level: Optional[str] = None,
    group_id: Optional[str] = None,
    parent_id: Optional[str] = None,
    is_superuser: bool = False,
) -> Dict[str, Any]:
    """``path`` sigue el sentinel ``_UNSET`` (ausente = sin cambio); ``""``/``None``
    explícito pone la columna a ``NULL`` (nodo agrupador sin layout)."""
    level = _level_of(sid)
    model = _LEVEL_MODEL[level]
    row = (await db.execute(select(model).where(model.id == sid))).scalar_one_or_none()
    if row is None:
        raise KeyError(f"unknown admin section: {sid}")

    if await _is_protected_section(db, sid):
        raise ProtectedResourceError(
            "the admin sections screen is protected and cannot be edited"
        )

    await _require_visibility(
        db, visibility_level=row.visibility_level, is_superuser=is_superuser
    )
    if await _is_admin_subtree(db, sid) and not is_superuser:
        raise ForbiddenVisibilityError(
            "forbidden: the admin group is restricted to superusers"
        )

    if visibility_level is not None:
        if visibility_level not in VISIBILITY_LEVELS:
            raise ValueError(f"visibility_level debe ser uno de {VISIBILITY_LEVELS}")
        row.visibility_level = visibility_level

    if label is not None:
        row.label = label
    if section_type is not None:
        row.section_type = section_type

    if system_name is not None:
        clash = (
            await db.execute(
                select(model).where(model.system_name == system_name, model.id != sid)
            )
        ).scalar_one_or_none()
        if clash is not None:
            raise _DuplicateError(f"system_name already exists: {system_name!r}")
        row.system_name = system_name

    if path is not _UNSET:
        new_path = path or None
        if new_path is not None:
            if not new_path.startswith("/"):
                raise ValueError(f"path debe empezar con '/': {new_path!r}")
            for lvl, mdl in _LEVEL_MODEL.items():
                query = select(mdl).where(mdl.path == new_path)
                if lvl == level:
                    query = query.where(mdl.id != sid)
                clash = (await db.execute(query)).scalar_one_or_none()
                if clash is not None:
                    raise _DuplicateError(f"path already exists: {new_path!r}")
        row.path = new_path

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
        if target.system_name == ADMIN_GROUP_SYSTEM_NAME and not is_superuser:
            raise ForbiddenVisibilityError(
                "forbidden: the admin group is restricted to superusers"
            )
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
    return await get_section(db, sid, is_superuser=True)


class _CycleError(ValueError):
    pass


CycleError = _CycleError


async def delete_section(db: AsyncSession, sid: str, *, is_superuser: bool) -> None:
    level = _level_of(sid)
    model = _LEVEL_MODEL[level]
    row = (await db.execute(select(model).where(model.id == sid))).scalar_one_or_none()
    if row is None:
        raise KeyError(f"unknown admin section: {sid}")

    if await _is_protected_section(db, sid):
        raise ProtectedResourceError(
            "the admin sections screen is protected and cannot be deleted"
        )

    await _require_visibility(
        db, visibility_level=row.visibility_level, is_superuser=is_superuser
    )
    if await _is_admin_subtree(db, sid) and not is_superuser:
        raise ForbiddenVisibilityError(
            "forbidden: the admin group is restricted to superusers"
        )

    if level in (1, 2):
        child_model = _LEVEL_MODEL[level + 1]
        parent_col = "parent_l1_id" if level == 1 else "parent_l2_id"
        child_count = (
            await db.execute(
                select(func.count()).select_from(child_model).where(
                    getattr(child_model, parent_col) == sid
                )
            )
        ).scalar_one()
        if child_count:
            raise HasChildrenError(
                f"section {sid} has {child_count} child section(s); move or delete them first"
            )

    owner_col = getattr(AdminView, _OWNER_COL[level])
    view_count = (
        await db.execute(select(func.count()).select_from(AdminView).where(owner_col == sid))
    ).scalar_one()
    if view_count:
        raise HasViewsError(
            f"section {sid} owns {view_count} view(s); reassign them to another section first"
        )

    await db.delete(row)
    await db.flush()
    await db.commit()
    invalidate_cache()


async def move_section(
    db: AsyncSession,
    sid: str,
    *,
    target_level: int,
    target_parent_id: str,
    is_superuser: bool,
) -> Dict[str, Any]:
    level = _level_of(sid)
    if target_level == level:
        raise ValueError("target_level must differ from the current level")
    if target_level not in (1, 2, 3):
        raise ValueError("target_level debe ser 1, 2 o 3")

    model = _LEVEL_MODEL[level]
    row = (await db.execute(select(model).where(model.id == sid))).scalar_one_or_none()
    if row is None:
        raise KeyError(f"unknown admin section: {sid}")

    if await _is_protected_section(db, sid):
        raise ProtectedResourceError("protected, cannot be moved")

    if level in (1, 2):
        child_model = _LEVEL_MODEL[level + 1]
        parent_col = "parent_l1_id" if level == 1 else "parent_l2_id"
        child_count = (
            await db.execute(
                select(func.count()).select_from(child_model).where(
                    getattr(child_model, parent_col) == sid
                )
            )
        ).scalar_one()
        if child_count:
            raise HasChildrenError(
                f"section {sid} has {child_count} child section(s); move or delete them "
                "first (moving a section with children between levels is not supported yet)"
            )

    if target_level == 1:
        target = (
            await db.execute(
                select(AdminSectionGroup).where(AdminSectionGroup.id == target_parent_id)
            )
        ).scalar_one_or_none()
        if target is None:
            raise ValueError(f"unknown section group: {target_parent_id}")
        target_is_admin = target.system_name == ADMIN_GROUP_SYSTEM_NAME
    else:
        parent_level_expected = target_level - 1
        target_prefix_level = _level_of(target_parent_id)
        if target_prefix_level != parent_level_expected:
            raise ValueError(
                f"target_parent_id must be a level {parent_level_expected} section"
            )
        parent_model = _LEVEL_MODEL[parent_level_expected]
        target = (
            await db.execute(
                select(parent_model).where(parent_model.id == target_parent_id)
            )
        ).scalar_one_or_none()
        if target is None:
            raise ValueError(f"unknown parent section: {target_parent_id}")
        target_is_admin = await _is_admin_subtree(db, target_parent_id)

    await _require_visibility(
        db, visibility_level=row.visibility_level, is_superuser=is_superuser
    )
    if await _is_admin_subtree(db, sid) and not is_superuser:
        raise ForbiddenVisibilityError(
            "forbidden: the admin group is restricted to superusers"
        )
    if target_is_admin and not is_superuser:
        raise ForbiddenVisibilityError(
            "forbidden: the admin group is restricted to superusers"
        )

    previous_id = row.id
    target_model = _LEVEL_MODEL[target_level]
    sibling_filter_col = "group_id" if target_level == 1 else _PARENT_COL[target_level]
    max_sort = (
        await db.execute(
            select(func.max(target_model.sort_order)).where(
                getattr(target_model, sibling_filter_col) == target_parent_id
            )
        )
    ).scalar()
    new_sort_order = (max_sort + 10) if max_sort is not None else 10

    new_kwargs: Dict[str, Any] = dict(
        system_name=row.system_name,
        label=row.label,
        path=row.path,
        section_type=row.section_type,
        sort_order=new_sort_order,
        visibility_level=row.visibility_level,
        origin=row.origin,
    )
    if target_level == 1:
        new_kwargs["group_id"] = target_parent_id
    elif target_level == 2:
        new_kwargs["parent_l1_id"] = target_parent_id
    else:
        new_kwargs["parent_l2_id"] = target_parent_id

    new_row = target_model(**new_kwargs)
    db.add(new_row)
    await db.flush()
    new_id = new_row.id

    owner_col_old = _OWNER_COL[level]
    owner_col_new = _OWNER_COL[target_level]
    views = list(
        (
            await db.execute(
                select(AdminView).where(getattr(AdminView, owner_col_old) == sid)
            )
        ).scalars()
    )
    for view in views:
        setattr(view, owner_col_old, None)
        setattr(view, owner_col_new, new_id)

    await db.delete(row)
    await db.flush()
    await db.commit()
    invalidate_cache()

    detail = await get_section(db, new_id, is_superuser=True)
    detail["previous_id"] = previous_id
    return detail


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


async def update_view(
    db: AsyncSession,
    view_id: str,
    *,
    responsible: Any = _UNSET,
    instructions: Any = _UNSET,
    owner_l1_id: Any = _UNSET,
    owner_l2_id: Any = _UNSET,
    owner_l3_id: Any = _UNSET,
) -> Dict[str, Any]:
    """ADR-023 (corrección) §2: ``owner_l{1,2,3}_id`` reasignan la sección dueña.

    Si NINGUNO de los 3 viene (los 3 son ``_UNSET``), el owner actual no se
    toca. Si ALGUNO viene, se arma el trío completo a partir de lo presente
    (ausentes ⇒ ``None`` en el trío nuevo) — mover de L1 a L2 basta con
    ``owner_l2_id=...``.
    """
    if (
        responsible is _UNSET
        and instructions is _UNSET
        and owner_l1_id is _UNSET
        and owner_l2_id is _UNSET
        and owner_l3_id is _UNSET
    ):
        raise EmptyViewUpdateError(
            "update requiere responsible_agent_profile_id y/o instructions y/o owner_l{1,2,3}_id"
        )
    view, section, level = await _view_with_section(db, view_id)

    if responsible is not _UNSET:
        value = (responsible or "").strip()
        view.responsible_agent_profile_id = resolve_responsible(value) if value else None

    if instructions is not _UNSET:
        text_value = (instructions or "").strip()
        view.instructions = text_value or None

    owner_touched = not (
        owner_l1_id is _UNSET and owner_l2_id is _UNSET and owner_l3_id is _UNSET
    )
    if owner_touched:
        new_l1 = owner_l1_id if owner_l1_id is not _UNSET else None
        new_l2 = owner_l2_id if owner_l2_id is not _UNSET else None
        new_l3 = owner_l3_id if owner_l3_id is not _UNSET else None

        if new_l1:
            target_level, target_model, target_id = 1, AdminSectionL1, new_l1
        elif new_l2:
            target_level, target_model, target_id = 2, AdminSectionL2, new_l2
        else:
            target_level, target_model, target_id = 3, AdminSectionL3, new_l3

        target = (
            await db.execute(select(target_model).where(target_model.id == target_id))
        ).scalar_one_or_none()
        if target is None:
            raise UnknownSectionTargetError(target_id)

        owner_col = _OWNER_COL[target_level]
        clash = (
            await db.execute(
                select(AdminView).where(
                    getattr(AdminView, owner_col) == target_id,
                    AdminView.key == view.key,
                    AdminView.id != view.id,
                )
            )
        ).scalar_one_or_none()
        if clash is not None:
            raise DuplicateViewKeyError(target_id, view.key)

        view.owner_l1_id = new_l1
        view.owner_l2_id = new_l2
        view.owner_l3_id = new_l3

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
