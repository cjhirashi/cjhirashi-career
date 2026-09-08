"""Override de herramientas por perfil (código por defecto ∩ override Admin).

Modelo análogo al prompt suffix (`profile_prompts.py`): el default vive en
`agent_profiles.py` (nivel + `allowed_tool_names`), y el Admin puede reemplazar el
set completo desde el catálogo. `delegate_to_specialist` no es editable — se aplica
por nivel (D-2).
"""
from typing import Dict, List, Optional, Sequence, Set

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.bedrock_agent_profile_tool import BedrockAgentProfileTool
from services.bedrock.agent_profiles import AgentProfile, get_profile, tools_for_profile
from services.bedrock import tools as bedrock_tools


def default_tool_names(profile: AgentProfile) -> Set[str]:
    """Set por defecto derivado del código (nivel + allowed_tool_names)."""
    return set(tools_for_profile(profile, bedrock_tools.all_tool_names()))


def effective_tool_names(
    profile: AgentProfile,
    override: Optional[Sequence[str]],
    *,
    section_tools: Optional[Set[str]] = None,
) -> Set[str]:
    """Set efectivo de herramientas para un turno.

    - **L2 (spec 004):** si se pasa `section_tools` (unión de las secciones que
      el agente posee), ese es el set base — no hay override directo para L2.
    - **L1/L3 (feature 003):** `override` reemplaza el default de código (D-1);
      `None` = default.
    - En todos los casos, `delegate_to_specialist` se aplica por nivel (D-2).
    """
    if section_tools is not None and profile.level == 2:
        names = set(section_tools) & bedrock_tools.all_tool_names()
    elif override is None:
        names = default_tool_names(profile)
    else:
        names = set(override) & bedrock_tools.all_tool_names()
    if profile.can_delegate:
        names.add("delegate_to_specialist")
    else:
        names.discard("delegate_to_specialist")
    return names


async def resolve_effective_tools(db: AsyncSession, profile: AgentProfile) -> tuple[Set[str], List[str]]:
    """Resuelve, **una vez por turno**, el set efectivo de herramientas y los
    ids de sección del caller (spec 004, RF-002 / RNF-001).

    - **L2:** unión de las herramientas derivadas de todas sus secciones
      (`section_catalog.derived_tools_for_agent`); `section_ids` = las que posee.
    - **L1/L3:** override directo (`bedrock_agent_profile_tools`) o default de
      código; `section_ids` = `[]`.
    """
    from services import section_catalog

    if profile.level == 2:
        section_tools = await section_catalog.derived_tools_for_agent(db, profile.id)
        sections = await section_catalog.sections_for_agent(db, profile.id)
        section_ids = [s["id"] for s in sections]
        return effective_tool_names(profile, None, section_tools=section_tools), section_ids

    override = await get_tool_override(db, profile.id)
    return effective_tool_names(profile, override), []


def validate_tool_names(tool_names: Sequence[str]) -> List[str]:
    """Normaliza (ordenado, sin duplicados) y valida contra el catálogo.

    Lanza `ValueError` si algún nombre no existe (feature 003 RF-004) o si es
    `scope=="section"` — esas sólo llegan a un agente vía su sección, no se
    asignan directo a L1/L3 (spec 004 RF-011).
    """
    cleaned = sorted(set(tool_names))
    unknown = set(cleaned) - bedrock_tools.all_tool_names()
    if unknown:
        raise ValueError(f"Unknown tool names: {sorted(unknown)}")
    section_only = sorted(t for t in cleaned if bedrock_tools.tool_scope(t) == "section")
    if section_only:
        raise ValueError(
            f"Tools de sección no asignables directo a un agente: {section_only}. "
            "Se reciben ligando el agente a la sección."
        )
    return cleaned


def list_builtin_tool_catalog() -> List[Dict[str, str]]:
    """Catálogo read-only de tools integradas (name + description + scope) — RF-009/010."""
    return [
        {
            "name": tool["name"],
            "description": tool["description"],
            "scope": bedrock_tools.tool_scope(tool["name"]),
        }
        for tool in bedrock_tools._RAW_TOOLS
    ]


async def get_tool_override(db: AsyncSession, profile_id: str) -> Optional[List[str]]:
    result = await db.execute(
        select(BedrockAgentProfileTool).where(
            BedrockAgentProfileTool.profile_id == profile_id
        )
    )
    row = result.scalar_one_or_none()
    if row is None or row.tool_names is None:
        return None
    return [str(x) for x in row.tool_names]


async def list_tool_overrides(db: AsyncSession) -> Dict[str, List[str]]:
    """Mapa profile_id → tool_names (solo filas con override presente)."""
    result = await db.execute(select(BedrockAgentProfileTool))
    return {
        row.profile_id: [str(x) for x in row.tool_names]
        for row in result.scalars().all()
        if row.tool_names is not None
    }


async def get_tool_state(db: AsyncSession, profile: AgentProfile) -> Dict[str, object]:
    defaults = default_tool_names(profile)

    if profile.level == 2:
        # spec 004: un L2 recibe herramientas de sus secciones (derivadas,
        # lectura). Sin override directo; `by_section` da la procedencia.
        from services import section_catalog
        from services.admin_sections import get_section_spec, tools_for_section

        sections = await section_catalog.sections_for_agent(db, profile.id)
        by_section = []
        union: set = set()
        for item in sections:
            try:
                spec = get_section_spec(item["id"])
            except KeyError:
                continue
            stools = tools_for_section(spec)
            union |= stools
            by_section.append(
                {"section_id": spec.id, "label": spec.label, "tools": sorted(stools)}
            )
        effective = effective_tool_names(profile, None, section_tools=union)
        return {
            "profile_id": profile.id,
            "default_tools": sorted(defaults),
            "override_tools": None,
            "effective_tools": sorted(effective),
            "by_section": by_section,
        }

    override = await get_tool_override(db, profile.id)
    effective = effective_tool_names(profile, override)
    return {
        "profile_id": profile.id,
        "default_tools": sorted(defaults),
        "override_tools": sorted(override) if override is not None else None,
        "effective_tools": sorted(effective),
        "by_section": None,
    }


async def set_tool_override(
    db: AsyncSession,
    profile_id: str,
    tool_names: Optional[Sequence[str]],
) -> Dict[str, object]:
    profile = get_profile(profile_id)
    profile_id = profile.id
    if profile.level == 2:
        # spec 004: un L2 recibe sus herramientas de sus secciones (derivadas).
        raise ValueError(
            "Un agente L2 no tiene override directo de herramientas; se derivan de sus secciones."
        )
    cleaned = validate_tool_names(tool_names) if tool_names is not None else None

    result = await db.execute(
        select(BedrockAgentProfileTool).where(
            BedrockAgentProfileTool.profile_id == profile_id
        )
    )
    row = result.scalar_one_or_none()
    if cleaned is None:
        if row:
            await db.delete(row)
            await db.commit()
    else:
        if row:
            row.tool_names = cleaned
        else:
            db.add(BedrockAgentProfileTool(profile_id=profile_id, tool_names=cleaned))
        await db.commit()
    return await get_tool_state(db, profile)
