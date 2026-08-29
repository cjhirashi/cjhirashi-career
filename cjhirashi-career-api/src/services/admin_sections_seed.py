"""Seeder de arranque de la jerarquía de secciones del Admin (ADR-022; ADR-023 corrección).

Desde ADR-023 (corrección) el CRUD de grupos y secciones L1/L2/L3 es 100% Admin
(ver ``services/section_catalog.py``): el seeder de código deja de sembrar y
podar esas 65 filas tras el arranque inicial (la migración ``c4d5e6f7a8b9``, o
esta misma alta idempotente, las siembran UNA vez). Lo único que sigue
corriendo en cada arranque es:

1. ``ensure_admin_group_and_section`` — alta **idempotente** (nunca UPDATE/prune)
   del grupo + sección protegidos ``admin``/``admin-sections``. Usa los mismos
   IDs fijos (``grp-12``/``s1-55``) que la migración nueva
   (``<rev>_admin_sections_crud_is_superuser.py``) para que, si ambos caminos
   llegan a competir (migración no corrida todavía en un entorno nuevo),
   converjan en el mismo valor — el `system_name` es lo que realmente evita el
   duplicado.
2. ``sync_views`` — upsert + prune de ``admin_views`` por ``(owner_l1_id, key)``,
   igual que siempre (las vistas siguen naciendo en código). Ya NO crea la
   sección dueña si falta (el operador pudo haberla borrado/movido) — solo
   loguea un warning y sigue.

Contrato invariante (sin cambio):
- **NUNCA** escribe ``admin_views.responsible_agent_profile_id`` ni
  ``admin_views.instructions`` (columnas del operador) salvo la alta inicial
  vía migración.
- Vistas: upsert por ``(owner_l1_id, key)`` de TODAS las columnas de código.
- Prune de vistas: solo filas ``origin='code'`` ausentes del registro (sin
  cambio respecto a ADR-022).
"""
from __future__ import annotations

import logging
from typing import Dict, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.admin_section_group import AdminSectionGroup
from models.admin_section_l1 import AdminSectionL1
from models.admin_view import AdminView
from services.admin_sections import list_section_specs
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

# ADR-023 (corrección) §5.1 — IDs congelados, siguientes libres tras
# _FROZEN_GROUPS (grp-1..grp-11) y _SEC_TO_S1 (s1-1..s1-54) de c4d5e6f7a8b9.
# Deben coincidir exactamente con los que usa la migración
# <rev>_admin_sections_crud_is_superuser.py.
ADMIN_GROUP_ID = "grp-12"
ADMIN_SECTION_ID = "s1-55"
ADMIN_GROUP_SYSTEM_NAME = "admin"
ADMIN_SECTION_SYSTEM_NAME = "admin-sections"
ADMIN_SECTION_PATH = "/settings/sections"


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


async def ensure_admin_group_and_section(session: AsyncSession) -> None:
    """Alta idempotente del grupo + sección protegidos ``admin``. NUNCA hace UPDATE.

    Si ya existen (sembrados por la migración o por un arranque anterior), no
    se toca nada — ni siquiera para refrescar ``label``/``path``: a partir de
    la migración esa fila es 100% propiedad del operador, igual que cualquier
    otra sección/grupo.
    """
    group = (
        await session.execute(
            select(AdminSectionGroup).where(
                AdminSectionGroup.system_name == ADMIN_GROUP_SYSTEM_NAME
            )
        )
    ).scalar_one_or_none()
    if group is None:
        group = AdminSectionGroup(
            id=ADMIN_GROUP_ID,
            system_name=ADMIN_GROUP_SYSTEM_NAME,
            name="Administración",
            sort_order=0,
            origin="code",
            visibility_level="superuser",
        )
        session.add(group)
        await session.flush()

    section = (
        await session.execute(
            select(AdminSectionL1).where(
                AdminSectionL1.system_name == ADMIN_SECTION_SYSTEM_NAME
            )
        )
    ).scalar_one_or_none()
    if section is None:
        # En BD con datos previos de c4d5e6f7a8b9, s1-17 ya existe con la misma
        # path pero system_name='settings-sections'. Lo migramos en vez de insertar
        # s1-55 (que colisionaría con el índice UNIQUE de path).
        existing_by_path = (
            await session.execute(
                select(AdminSectionL1).where(
                    AdminSectionL1.path == ADMIN_SECTION_PATH
                )
            )
        ).scalar_one_or_none()
        if existing_by_path is not None:
            # Migrar s1-17 (legacy 'settings-sections') al grupo admin.
            # Se renombra a 'admin-sections' para que sync_views lo encuentre
            # con el system_name canónico que usa list_section_specs().
            existing_by_path.group_id = group.id
            existing_by_path.system_name = ADMIN_SECTION_SYSTEM_NAME
            existing_by_path.visibility_level = "superuser"
            await session.flush()
        else:
            session.add(
                AdminSectionL1(
                    id=ADMIN_SECTION_ID,
                    group_id=group.id,
                    system_name=ADMIN_SECTION_SYSTEM_NAME,
                    label="Secciones del Admin",
                    path=ADMIN_SECTION_PATH,
                    section_type="table",
                    sort_order=0,
                    origin="code",
                    visibility_level="superuser",
                )
            )
            await session.flush()


async def sync_views(session: AsyncSession) -> None:
    """Upsert + prune de ``admin_views`` por ``(owner_l1_id, key)`` (sin cambio de lógica).

    A diferencia de ADR-022, ya NO crea la sección L1 dueña si falta en la BD
    — resuelve el owner contra lo que ya exista (creado por migración o por el
    operador vía API); si una sección de código fue borrada/movida por el
    operador, sus vistas de código dejan de sincronizarse (warning en log, sin
    excepción).
    """
    specs = list_section_specs()

    l1_by_system: Dict[str, AdminSectionL1] = {
        s.system_name: s
        for s in (await session.execute(select(AdminSectionL1))).scalars()
    }

    views_by_owner: Dict[str, Dict[str, AdminView]] = {}
    for view in (await session.execute(select(AdminView))).scalars():
        if view.owner_l1_id:
            views_by_owner.setdefault(view.owner_l1_id, {})[view.key] = view

    for spec in specs:
        l1 = l1_by_system.get(spec.system_name)
        if l1 is None:
            logger.warning(
                "sync_views: sección de código %r ya no existe en BD (borrada "
                "por el operador); sus vistas de código no se sincronizan",
                spec.system_name,
            )
            continue

        owner_id = l1.id
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
