"""
System prompt — default, override PG, suffix por perfil y sección.
"""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.bedrock_settings import BedrockSettings
from services.bedrock.agent_profiles import (
    AgentProfile,
    AGENT_SEARCH_OPERATIONS,
    AGENT_VACANCY_SEARCH,
    delegation_targets,
)
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
    "Antes de afirmar algo sobre un registro concreto (ej. ach-17, vac-5), consulta "
    "herramientas o el especialista dueño del dominio. Si la herramienta o el sub-turno "
    "devuelve not_found o vacío, dilo — no rellenes con suposiciones. Los IDs son "
    "prefijados (ach-17, cmp-42, trl-3)."
)

_L1_ORCHESTRATION_RULE = (
    "Nivel 1: no tienes CRUD ni tools de tarea. Cada pedido de datos o escritura "
    "se resuelve con delegate_to_specialist al L2 de esa área o al L3 de esa tarea. "
    "No respondas listados ni cifras de carrera sin haber delegado en este turno."
)

_L2_DOMAIN_RULE = (
    "Nivel 2: opera solo tu dominio. No llames a otro L2 ni al orquestador. "
    "Tareas transversales (bitácora, PDF de un registro, imágenes, plan de tareas, "
    "publicación LinkedIn, discovery de vacantes, redacción de CV o cover letter, "
    "consulta web, repos GitHub) se delegan a L3. "
    "Si piden listar TODO un recurso de tu dominio, usa list_career_record con limit=100 y pagina mientras "
    "has_more sea true. "
    "Si preguntan CUÁNTOS hay, llama count_career_records. "
    "Redactar en el chat no persiste: usa create_career_record o update_career_record "
    "(en diseño PDF: pdf_style / pdf_template). No afirmes que guardaste hasta que la tool "
    "devuelva el id. Si el usuario confirma (procede, adelante, hazlo), llama la tool en este turno."
)

_L3_TASK_RULE = (
    "Nivel 3: no hablas con el usuario. Ejecuta la tarea con tus tools y devuelve "
    "un resumen factual (ids, URLs, errores). No delegues."
)


def _delegation_catalog_block(profile: AgentProfile) -> str:
    targets = delegation_targets(profile)
    if not targets:
        return ""
    lines = [f"- {p.id} (L{p.level}) — {p.label}" for p in targets]
    return "Especialistas a los que puedes delegar:\n" + "\n".join(lines)


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
    parts = [base, "Las reglas de nivel de este perfil tienen prioridad sobre el prompt global si hay conflicto.", GROUNDING_RULE, suffix]
    if page_context and page_context.get("resource_key"):
        title = page_context.get("page_title") or page_context["resource_key"]
        parts.append(
            f"El usuario está en {title} (resource_key={page_context['resource_key']}). "
            "Prioriza operaciones sobre ese recurso salvo que pida otra cosa."
        )
    route = (page_context or {}).get("route") or ""
    if profile.level == 1:
        parts.append(_L1_ORCHESTRATION_RULE)
        parts.append(_delegation_catalog_block(profile))
    elif profile.level == 2:
        parts.append(_L2_DOMAIN_RULE)
        parts.append(_delegation_catalog_block(profile))
    else:
        parts.append(_L3_TASK_RULE)
    if profile.id in (AGENT_SEARCH_OPERATIONS, AGENT_VACANCY_SEARCH) or route == "/job-discovery":
        parts.append(JOB_DISCOVERY_AUTH_RULE)
    return "\n\n".join(p for p in parts if p)
