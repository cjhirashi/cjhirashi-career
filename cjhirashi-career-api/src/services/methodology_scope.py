"""Alcance de una metodología operativa a uno o más agentes."""
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.bedrock.agent_profiles import AGENT_METHODOLOGIES


def applies_to_caller(
    agent_profile_ids: Optional[Any],
    section_ids: Optional[Any],
    caller_profile_id: Optional[str],
    caller_section_ids: Optional[Any],
) -> bool:
    """True si la metodología es visible para el caller (spec 004).

    - compartida (`agent_profile_ids` y `section_ids` ambos vacíos/null) → todos.
    - guardián `agent_methodologies` → todas.
    - L1/L3 → si su id está en `agent_profile_ids`.
    - L2 → si alguna de sus secciones (`caller_section_ids`) está en `section_ids`.
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


def applies_to_agent(agent_profile_ids: Optional[Any], caller_profile_id: Optional[str]) -> bool:
    """Compat (feature 003): visibilidad por `agent_profile_ids` solamente.

    Equivale a `applies_to_caller(agent_profile_ids, None, caller, None)`.
    Los call sites con contexto de sección usan `applies_to_caller` directamente.
    """
    return applies_to_caller(agent_profile_ids, None, caller_profile_id, None)


def strip_l2_from_agent_ids(ids: Optional[Any]) -> List[str]:
    """Quita los ids de agentes L2 de una lista `agent_profile_ids` (spec 004:
    los L2 reciben metodologías vía sección). Ids desconocidos se conservan."""
    from services.bedrock.agent_profiles import get_profile

    out: List[str] = []
    for x in ids or []:
        try:
            if get_profile(x).level == 2:
                continue
        except KeyError:
            pass
        out.append(x)
    return out


def is_shared_methodology(agent_profile_ids: Optional[Any]) -> bool:
    """True si la metodología aplica a todos los agentes (lista vacía o null)."""
    ids = agent_profile_ids or []
    return not isinstance(ids, list) or not ids


def next_agent_profile_ids(
    current_ids: Optional[Any],
    profile_id: str,
    should_apply: bool,
    all_profile_ids: set[str],
) -> Optional[List[str]]:
    """Nueva lista `agent_profile_ids`, o None si no hay que persistir.

    Vacío = compartida (todos). Al desasignar el último dueño exclusivo se
    aparca en `agent_methodologies` para no volver a compartirla con el
    agente que se acaba de quitar.
    """
    current = [item for item in (current_ids or []) if item]
    shared = not current
    currently_assigned = shared or profile_id in current
    if currently_assigned == should_apply:
        return None
    if should_apply:
        return current + [profile_id]
    if shared:
        return sorted(all_profile_ids - {profile_id})
    remaining = [item for item in current if item != profile_id]
    if remaining:
        return remaining
    if profile_id != AGENT_METHODOLOGIES:
        return [AGENT_METHODOLOGIES]
    return []


async def list_methodologies_for_catalog(
    db: AsyncSession,
    user_id: str,
    caller_profile_id: str,
) -> List[Dict[str, Any]]:
    """Todas las metodologías del usuario, con flag de asignación al caller."""
    from models.operational_methodology import OperationalMethodology

    result = await db.execute(
        select(
            OperationalMethodology.id,
            OperationalMethodology.title,
            OperationalMethodology.section,
            OperationalMethodology.agent_profile_ids,
        )
        .where(OperationalMethodology.user_id == user_id)
        .order_by(OperationalMethodology.title.asc())
    )
    items: List[Dict[str, Any]] = []
    for row in result.all():
        shared = is_shared_methodology(row.agent_profile_ids)
        ids = row.agent_profile_ids or []
        assigned = shared or (isinstance(ids, list) and caller_profile_id in ids)
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


async def set_agent_methodologies(
    db: AsyncSession,
    user_id: str,
    profile_id: str,
    methodology_ids: List[str],
) -> List[Dict[str, Any]]:
    """Asigna al agente exactamente las metodologías de `methodology_ids`."""
    from models.operational_methodology import OperationalMethodology
    from repositories.career_repository import CareerRepository
    from services.bedrock.agent_profiles import get_profile, known_agent_profile_ids

    profile_id = get_profile(profile_id).id

    wanted = set(methodology_ids)
    all_ids = known_agent_profile_ids()
    result = await db.execute(
        select(OperationalMethodology).where(OperationalMethodology.user_id == user_id)
    )
    repo = CareerRepository(
        OperationalMethodology,
        resource_key="operational-methodologies",
        vectorize=True,
    )
    for row in result.scalars().all():
        nxt = next_agent_profile_ids(
            row.agent_profile_ids,
            profile_id,
            row.id in wanted,
            all_ids,
        )
        if nxt is None:
            continue
        await repo.update_for_user(db, user_id, row.id, {"agent_profile_ids": nxt})
    # Re-index EVERY methodology of this user in Qdrant, awaited, even when no
    # `agent_profile_ids` changed above. The catalog injected into the prompt
    # reads straight from Postgres and was already correct; the bug (spec 003
    # reopening, RF-014) is that `search_knowledge_base type=methodology` reads
    # Qdrant, whose index drifted. Forcing the re-index here makes every save
    # from the agent catalog self-heal the vector store.
    await repo.reindex_for_user(db, user_id)
    return await list_methodologies_for_catalog(db, user_id, profile_id)


async def list_assigned_methodologies(
    db: AsyncSession,
    user_id: str,
    caller_profile_id: str,
    caller_section_ids: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Catálogo de metodologías que el caller debe consultar.

    L2: por las secciones que posee (`caller_section_ids`). L1/L3: por
    `agent_profile_ids`. Más las compartidas. Cada item trae su `section_ids`
    de procedencia para poder agruparlo en el prompt (spec 004, RF-008).
    """
    from models.operational_methodology import OperationalMethodology

    result = await db.execute(
        select(
            OperationalMethodology.id,
            OperationalMethodology.title,
            OperationalMethodology.section,
            OperationalMethodology.agent_profile_ids,
            OperationalMethodology.section_ids,
        )
        .where(OperationalMethodology.user_id == user_id)
        .order_by(OperationalMethodology.title.asc())
    )
    assigned: List[Dict[str, Any]] = []
    for row in result.all():
        if applies_to_caller(
            row.agent_profile_ids, row.section_ids, caller_profile_id, caller_section_ids
        ):
            a_ids = row.agent_profile_ids if isinstance(row.agent_profile_ids, list) else []
            s_ids = row.section_ids if isinstance(row.section_ids, list) else []
            assigned.append(
                {
                    "id": row.id,
                    "title": row.title,
                    "section": row.section,
                    "section_ids": s_ids,
                    "shared": not a_ids and not s_ids,
                }
            )
    return assigned
