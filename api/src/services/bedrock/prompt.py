"""
System prompt — default, override PG, suffix por perfil y sección.
"""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.bedrock_settings import BedrockSettings
from services.bedrock.agent_profiles import AgentProfile


def default_system_prompt() -> str:
    return (
        "Eres Agent Bedrock, el asistente de IA del gestor de carrera de Carlos Jiménez Hirashi. "
        "Tienes acceso a herramientas CRUD sobre ~30 tablas de carrera y búsqueda semántica en Qdrant. "
        "Responde en español salvo que pidan otro idioma. Sé preciso con resource_key antes de escribir."
    )


async def get_system_prompt_override(db: AsyncSession) -> Optional[str]:
    result = await db.execute(select(BedrockSettings).limit(1))
    row = result.scalar_one_or_none()
    return row.system_prompt if row and row.system_prompt else None


async def compose_system_prompt(
    db: AsyncSession,
    profile: AgentProfile,
    page_context: Optional[dict],
) -> str:
    base = await get_system_prompt_override(db) or default_system_prompt()
    parts = [base, profile.system_prompt_suffix]
    if page_context and page_context.get("resource_key"):
        title = page_context.get("page_title") or page_context["resource_key"]
        parts.append(
            f"El usuario está en {title} (resource_key={page_context['resource_key']}). "
            "Prioriza operaciones sobre ese recurso salvo que pida otra cosa."
        )
    return "\n\n".join(p for p in parts if p)
