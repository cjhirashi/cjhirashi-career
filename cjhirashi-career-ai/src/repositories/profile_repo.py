"""
Repositorio de los overrides por perfil de agente: suffix de prompt, foto, tools y delegación.

Traslado de `profile_prompts.py`, `profile_photos.py`, `profile_tools.py` y
`profile_delegation.py` (API), reducido a persistencia: el catálogo de perfiles, la
validación de nombres y la intersección con el nivel viven en los servicios.
`None` = sin override (vale el default de código); una lista vacía es un override válido.
"""
from typing import Dict, List, Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.bedrock_agent_delegation import BedrockAgentDelegation
from models.bedrock_agent_profile_photo import BedrockAgentProfilePhoto
from models.bedrock_agent_profile_prompt import BedrockAgentProfilePrompt
from models.bedrock_agent_profile_tool import BedrockAgentProfileTool
from services.agent_profiles import filter_level_allowed, get_profile


# ---------------------------------------------------------------------------- prompts

async def get_prompt_suffix(db: AsyncSession, profile_id: str) -> Optional[str]:
    row = await db.get(BedrockAgentProfilePrompt, profile_id)
    if row and row.system_prompt_suffix.strip():
        return row.system_prompt_suffix.strip()
    return None


async def list_prompt_overrides(db: AsyncSession) -> Dict[str, str]:
    result = await db.execute(select(BedrockAgentProfilePrompt))
    return {row.profile_id: row.system_prompt_suffix for row in result.scalars().all()}


async def set_prompt_suffix(db: AsyncSession, profile_id: str, suffix: Optional[str]) -> None:
    """Fija el override; texto vacío o `None` lo elimina."""
    text = suffix.strip() if suffix else None
    row = await db.get(BedrockAgentProfilePrompt, profile_id)
    if not text:
        if row:
            await db.delete(row)
    elif row:
        row.system_prompt_suffix = text
    else:
        db.add(BedrockAgentProfilePrompt(profile_id=profile_id, system_prompt_suffix=text))
    await db.commit()


# ---------------------------------------------------------------------------- fotos

async def photos_map(db: AsyncSession) -> Dict[str, str]:
    result = await db.execute(select(BedrockAgentProfilePhoto))
    return {row.profile_id: row.photo_url for row in result.scalars().all() if row.photo_url}


async def set_photo(db: AsyncSession, profile_id: str, photo_url: Optional[str]) -> Optional[str]:
    url = (photo_url or "").strip() or None
    row = await db.get(BedrockAgentProfilePhoto, profile_id)
    if not url:
        if row:
            await db.delete(row)
            await db.commit()
        return None
    if row:
        row.photo_url = url
    else:
        db.add(BedrockAgentProfilePhoto(profile_id=profile_id, photo_url=url))
    await db.commit()
    return url


# ---------------------------------------------------------------------------- tools

async def get_tool_override(db: AsyncSession, profile_id: str) -> Optional[List[str]]:
    row = await db.get(BedrockAgentProfileTool, profile_id)
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


async def set_tool_override(db: AsyncSession, profile_id: str, tool_names: Optional[Sequence[str]]) -> None:
    """`None` elimina el override (vuelve al default de código)."""
    row = await db.get(BedrockAgentProfileTool, profile_id)
    if tool_names is None:
        if row:
            await db.delete(row)
    elif row:
        row.tool_names = list(tool_names)
    else:
        db.add(BedrockAgentProfileTool(profile_id=profile_id, tool_names=list(tool_names)))
    await db.commit()


# ---------------------------------------------------------------------------- delegación

async def list_delegation_overrides(db: AsyncSession) -> Dict[str, List[str]]:
    result = await db.execute(select(BedrockAgentDelegation))
    out: Dict[str, List[str]] = {}
    for row in result.scalars().all():
        ids = row.target_ids if isinstance(row.target_ids, list) else []
        out[row.profile_id] = [str(x) for x in ids]
    return out


async def get_delegation_override(db: AsyncSession, profile_id: str) -> Optional[List[str]]:
    return (await list_delegation_overrides(db)).get(profile_id)


async def set_delegation_override(db: AsyncSession, profile_id: str, target_ids: Optional[Sequence[str]]) -> None:
    """`None` elimina el override; una lista (incluso vacía) lo fija, filtrada por nivel como en la API.

    `KeyError` si el perfil no existe."""
    profile = get_profile(profile_id)
    if target_ids is not None:
        target_ids = filter_level_allowed(profile, target_ids)
    row = await db.get(BedrockAgentDelegation, profile_id)
    if target_ids is None:
        if row:
            await db.delete(row)
    elif row:
        row.target_ids = list(target_ids)
    else:
        db.add(BedrockAgentDelegation(profile_id=profile_id, target_ids=list(target_ids)))
    await db.commit()
