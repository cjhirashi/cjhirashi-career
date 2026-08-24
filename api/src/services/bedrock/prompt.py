"""
System prompt — default, override PG, suffix por perfil y sección.
"""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.bedrock_settings import BedrockSettings
from services.bedrock.agent_profiles import AgentProfile
from services.bedrock import profile_prompts

# ============================================================================
# Reglas de prompt del sistema
# ============================================================================

JOB_DISCOVERY_AUTH_RULE = (
    "Vacantes descubiertas: run_job_discovery solo hace preview (refs L1, L2…). "
    "Presenta empresa, rol, fuente y URL. No llames save_job_listings hasta que Carlos "
    "autorice refs concretas. save_job_listings(refs=...) crea vacancies pending_review "
    "para seguimiento en Vacantes. Nunca inventes vacantes ni uses create_career_record "
    "para ofertas de un discovery. Si Carlos pega una URL de vacante, importar y guardar "
    "esa ref sí está autorizado."
)

GROUNDING_RULE = (
    "REGLA CRÍTICA — NO ALUCINAR: Los datos de carrera viven en PostgreSQL, no en tu "
    "entrenamiento. Nunca inventes registros, IDs, títulos, fechas ni contenido. "
    "Antes de afirmar algo sobre un registro concreto (ej. ach-17, vac-5), llama "
    "get_career_record o list_career_record con search. Para preguntas abiertas usa "
    "search_knowledge_base. Si la herramienta devuelve not_found o vacío, dilo — no "
    "rellenes con suposiciones. Los IDs son prefijados (ach-17, cmp-42, trl-3). "
    "Si piden listar o enumerar TODO un recurso (logros, vacantes, proyectos…), usa "
    "list_career_record con limit=100 (sin search), pagina mientras has_more sea true, "
    "y menciona los total_count items en la respuesta — nunca elijas solo los que te "
    "parezcan más importantes. Si preguntan CUÁNTOS hay, llama count_career_records "
    "y responde con el número exacto antes de listar."
)


# ============================================================================
# Prompt base y override desde PG
# ============================================================================

def default_system_prompt() -> str:
    """Prompt base completo — misma fuente que /bedrock/instructions."""
    from services import bedrock_service

    return bedrock_service.default_system_prompt()


async def get_system_prompt_override(db: AsyncSession) -> Optional[str]:
    result = await db.execute(select(BedrockSettings).limit(1))
    row = result.scalar_one_or_none()
    return row.system_prompt if row and row.system_prompt else None


# ============================================================================
# Composición del system prompt
# ============================================================================

async def compose_system_prompt(
    db: AsyncSession,
    profile: AgentProfile,
    page_context: Optional[dict],
) -> str:
    base = await get_system_prompt_override(db) or default_system_prompt()
    suffix = await profile_prompts.get_effective_suffix(db, profile)
    parts = [base, GROUNDING_RULE, suffix]
    if page_context and page_context.get("resource_key"):
        title = page_context.get("page_title") or page_context["resource_key"]
        parts.append(
            f"El usuario está en {title} (resource_key={page_context['resource_key']}). "
            "Prioriza operaciones sobre ese recurso salvo que pida otra cosa."
        )
    route = (page_context or {}).get("route") or ""
    if profile.id in ("search", "orchestrator") or route == "/job-discovery":
        parts.append(JOB_DISCOVERY_AUTH_RULE)
    return "\n\n".join(p for p in parts if p)
