"""Seeder idempotente de la jerarquía de secciones del Admin (ADR-022).

``sync_structure`` alinea las 6 tablas reales con el registro de código
(``services/admin_sections.py``). Es idempotente y se llama desde
``database.init_db()`` tras ``create_all`` (dev/CI/tests, que no corren Alembic).
La migración ``c4d5e6f7a8b9`` reproduce esta misma estructura con un snapshot
CONGELADO embebido (no importa este módulo) y encima siembra la conversión de
``admin_section_overrides`` — un test verifica que ambos caminos producen el
mismo conjunto de filas.

Contrato invariante:
- **NUNCA** escribe ``admin_views.responsible_agent_profile_id`` ni
  ``admin_views.instructions`` (columnas del operador).
- Grupos: upsert por ``system_name``; INSERT trae el ``sort_order`` de código,
  UPDATE solo refresca ``name``.
- Secciones L1: upsert por ``system_name``; INSERT trae ``group_id``/``sort_order``
  de código, UPDATE solo ``label``/``path``/``section_type``.
- Vistas: upsert por ``(owner_l1_id, key)`` de TODAS las columnas de código.
- Prune: solo filas ``origin='code'`` ausentes del registro (el CASCADE de L1
  arrastra vistas y sub-secciones L2/L3).
"""
from __future__ import annotations

import logging
from typing import Dict, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.admin_section_group import AdminSectionGroup
from models.admin_section_l1 import AdminSectionL1
from models.admin_view import AdminView
from services.admin_sections import GROUPS, list_section_specs
from services.bedrock.agent_profiles import (
    AGENT_DIGITAL_PRESENCE,
    AGENT_GITHUB,
    AGENT_LINKEDIN_PUBLISHING,
    AGENT_SEARCH_OPERATIONS,
    AGENT_VACANCY_SEARCH,
)

logger = logging.getLogger(__name__)

# L3 (sin chat propio) → L1/L2 que lleva el chat contextual de esa sección.
# CONGELADO. Lo consume SOLO la migración, para sembrar
# ``responsible_agent_profile_id`` la primera vez. El seeder idempotente jamás
# escribe ese campo. Un fallback que resuelva a L1 (task_manager→orchestrator) o
# ausente (changelog) ⇒ NULL.
_L3_CHAT_FALLBACK: Dict[str, str] = {
    AGENT_LINKEDIN_PUBLISHING: AGENT_DIGITAL_PRESENCE,
    AGENT_VACANCY_SEARCH: AGENT_SEARCH_OPERATIONS,
    AGENT_GITHUB: AGENT_DIGITAL_PRESENCE,
}

_GROUP_SYSTEM_BY_NAME: Dict[str, str] = {name: system for _gid, system, name, _so in GROUPS}


def _frozen_view_id_map() -> Dict[Tuple[str, str], str]:
    """``(owner_l1_id, view_key) -> vw-N`` congelado por (entero de sección, orden de vista)."""
    mapping: Dict[Tuple[str, str], str] = {}
    counter = 0
    for spec in sorted(list_section_specs(), key=lambda s: int(s.id.split("-")[1])):
        for view in spec.views:
            counter += 1
            mapping[(spec.id, view.key)] = f"vw-{counter}"
    return mapping


VIEW_ID_MAP: Dict[Tuple[str, str], str] = _frozen_view_id_map()


async def sync_structure(session: AsyncSession) -> None:
    specs = list_section_specs()

    # --- Grupos ---------------------------------------------------------------
    groups_by_system = {
        g.system_name: g
        for g in (await session.execute(select(AdminSectionGroup))).scalars()
    }
    group_id_by_system: Dict[str, str] = {}
    for gid, system_name, name, sort_order in GROUPS:
        row = groups_by_system.get(system_name)
        if row is None:
            row = AdminSectionGroup(
                id=gid, system_name=system_name, name=name, sort_order=sort_order
            )
            session.add(row)
        else:
            row.name = name
        group_id_by_system[system_name] = row.id
    await session.flush()

    # --- Secciones L1 ------------------------------------------------------------
    l1_by_system = {
        s.system_name: s
        for s in (await session.execute(select(AdminSectionL1))).scalars()
    }
    wanted_l1: set[str] = set()
    l1_id_by_system: Dict[str, str] = {}
    for spec in specs:
        wanted_l1.add(spec.system_name)
        group_system = _GROUP_SYSTEM_BY_NAME[spec.group]
        row = l1_by_system.get(spec.system_name)
        if row is None:
            row = AdminSectionL1(
                id=spec.id,
                group_id=group_id_by_system[group_system],
                system_name=spec.system_name,
                label=spec.label,
                path=spec.path,
                section_type=spec.section_type,
                sort_order=spec.sort_order,
                origin="code",
            )
            session.add(row)
        else:
            row.label = spec.label
            row.path = spec.path
            row.section_type = spec.section_type
        l1_id_by_system[spec.system_name] = row.id
    await session.flush()

    for system_name, row in l1_by_system.items():
        if system_name not in wanted_l1 and row.origin == "code":
            logger.warning("admin_sections_seed: prune L1 %s (%s)", row.id, system_name)
            await session.delete(row)
    await session.flush()

    # --- Vistas ---------------------------------------------------------------
    views_by_owner: Dict[str, Dict[str, AdminView]] = {}
    for view in (await session.execute(select(AdminView))).scalars():
        if view.owner_l1_id:
            views_by_owner.setdefault(view.owner_l1_id, {})[view.key] = view

    for spec in specs:
        owner_id = l1_id_by_system[spec.system_name]
        current = views_by_owner.get(owner_id, {})
        wanted_keys: set[str] = set()
        for idx, view in enumerate(spec.views):
            wanted_keys.add(view.key)
            payload = dict(
                label=view.label,
                sort_order=idx,
                has_controls_window=view.has_controls_window,
                tool_names=list(view.tool_names),
                data_source=view.data_source,
                resource_key=view.resource_key,
            )
            row = current.get(view.key)
            if row is None:
                session.add(
                    AdminView(
                        id=VIEW_ID_MAP[(spec.id, view.key)],
                        owner_l1_id=owner_id,
                        key=view.key,
                        origin="code",
                        **payload,
                    )
                )
            else:
                for field_name, value in payload.items():
                    setattr(row, field_name, value)
        for key, row in current.items():
            if key not in wanted_keys and row.origin == "code":
                logger.warning(
                    "admin_sections_seed: prune view %s (%s/%s)", row.id, owner_id, key
                )
                await session.delete(row)
    await session.flush()
