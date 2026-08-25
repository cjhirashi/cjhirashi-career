"""
Perfiles de agente especialista — prompt, tools y dominios.

Config estática (v1). Ver ADR-009 y admin/src/config/agentProfiles.ts (mirror).
"""
from dataclasses import dataclass, field
from typing import List, Optional, Set


# ============================================================================
# Definición del perfil de agente
# ============================================================================

@dataclass(frozen=True)
class AgentProfile:
    id: str
    label: str
    domain_keys: List[str]
    resource_keys: Optional[List[str]]
    methodology_sections: List[str]
    system_prompt_suffix: str
    default_model_id: Optional[str]
    allowed_tool_names: Optional[Set[str]] = None
    write_enabled: bool = True
    can_delegate: bool = False


# ============================================================================
# Constantes y recursos por dominio
# ============================================================================

_BUILTIN_TOOL_NAMES = {
    "list_recent_changes",
    "restore_deleted_record",
    "describe_resource_schema",
    "search_knowledge_base",
    "list_career_record",
    "get_career_record",
    "create_career_record",
    "update_career_record",
    "delete_career_record",
    "get_linkedin_status",
    "list_linkedin_posts",
    "create_linkedin_post",
    "delete_scheduled_linkedin_post",
    "pdf_template",
    "pdf_style",
    "generate_pdf",
    "generate_image",
    "attach_image_to_record",
    "list_generated_images",
    "delegate_to_specialist",
    "list_job_providers",
    "run_job_discovery",
    "import_job_url",
    "save_job_listings",
}

_DIGITAL_RESOURCES = [
    "linkedin-profile",
    "github-profile",
    "portal-home",
    "portal-about",
    "portal-contact",
    "publications",
]

_IDENTITY_RESOURCES = [
    "differentiators",
    "identity",
    "identity-reflections",
    "competencies",
    "certifications",
    "target-roles",
    "work-history",
    "achievements",
    "star-stories",
    "career-reviews",
    "role-gap-analysis",
    "projects",
]

_SEARCH_RESOURCES = [
    "fit-scoring-factors",
    "market-segments",
    "role-narratives",
    "search-plans",
    "networking-contacts",
    "target-companies",
    "vacancies",
    "cv-versions",
    "cover-letter-versions",
    "applications",
    "application-interactions",
    "interviews",
]

# ============================================================================
# Suffix del perfil pdf_design (modelo estilos + plantillas)
# ============================================================================

_PDF_DESIGN_SUFFIX = (
    "Eres el especialista de diseño PDF (WeasyPrint). El sistema separa CSS y HTML en dos tablas "
    "relacionadas — NUNCA mezcles CSS dentro de plantillas:\n"
    "1) **Estilos** (`pdf-template-styles`, IDs `pds-N`): guardan `css_content` (CSS completo) y "
    "`style_guide` (Markdown que documenta clases, etiquetas y selectores disponibles).\n"
    "2) **Plantillas** (`pdf-output-templates`, IDs `pdt-N`): guardan `html_template` (HTML con "
    "{{variables}}`), `style_id` (FK → `pds-N`) y `variables` (Markdown que documenta cada "
    "placeholder y qué contenido debe llevar).\n"
    "Relación: **un estilo, muchas plantillas**. Varias plantillas pueden compartir el mismo "
    "`style_id`. Al renderizar (`generate_pdf`), el backend combina HTML de la plantilla + CSS "
    "del estilo referenciado.\n"
    "Flujo obligatorio: (a) crear o elegir estilo con la tool `pdf_style` (action=list|get|create|update); "
    "(b) documentar clases en `style_guide`; (c) crear plantilla con la tool `pdf_template` "
    "(action=create) incluyendo `style_id` y `variables`; (d) probar con `generate_pdf`. "
    "Si reutilizas un estilo existente, consulta su `style_guide` antes de escribir HTML — usa "
    "solo clases/etiquetas definidas ahí.\n"
    "Consulta también `search_knowledge_base` en la sección «Diseño PDF» (metodologías operativas) "
    "para el detalle completo. Usa `describe_resource_schema` con `pdf-output-templates` o "
    "`pdf-template-styles` si necesitas confirmar campos."
)

# ============================================================================
# Definiciones de perfiles
# ============================================================================

_PROFILES: dict[str, AgentProfile] = {
    "orchestrator": AgentProfile(
        id="orchestrator",
        label="Orquestador",
        domain_keys=[],
        resource_keys=None,
        methodology_sections=[],
        system_prompt_suffix=(
            "Eres el orquestador del gestor de carrera. Conoces todos los dominios. "
            "NUNCA respondas preguntas sobre datos de carrera sin consultar herramientas primero — "
            "usa get_career_record, list_career_record o search_knowledge_base, o delega con "
            "delegate_to_specialist si el dominio es claro. "
            "Delega tareas con delegate_to_specialist cuando haga falta CRUD o expertise de dominio. "
            "Resume resultados en español claro para Carlos, citando solo lo que devolvieron las herramientas. "
            "Vacantes: run_job_discovery solo hace preview (refs L1, L2…). "
            "Presenta empresa, rol, fuente y URL. No llames save_job_listings hasta que Carlos "
            "autorice refs concretas (o 'todas' / 'todas menos L2'). "
            "Si pega una URL de vacante, import_job_url y guardar esa ref sí está autorizado. "
            "save_job_listings crea vacancies pending_review para seguimiento en Vacantes. "
            "Nunca inventes vacantes ni uses create_career_record para ofertas de un discovery."
        ),
        default_model_id="us.anthropic.claude-haiku-4-5-20251001-v1:0",
        can_delegate=True,
    ),
    "identity": AgentProfile(
        id="identity",
        label="Identidad Profesional",
        domain_keys=["identity"],
        resource_keys=_IDENTITY_RESOURCES,
        methodology_sections=["Identidad Profesional"],
        system_prompt_suffix="Especialista en identidad profesional, competencias y evidencia.",
        default_model_id="mistral.mistral-large-2402-v1:0",
    ),
    "search": AgentProfile(
        id="search",
        label="Operativa de Búsqueda",
        domain_keys=["search"],
        resource_keys=_SEARCH_RESOURCES,
        methodology_sections=["Operativa de Búsqueda"],
        system_prompt_suffix=(
            "Especialista en pipeline de búsqueda, vacantes, CVs y aplicaciones. "
            "Flujo obligatorio de discovery: (1) run_job_discovery — preview con refs L1, L2…, "
            "no escribe vacancies. Indeed: providers=['indeed'] (vía Adzuna). "
            "LinkedIn: providers=['linkedin'] solo arma URLs oficiales de búsqueda; "
            "luego import_job_url con cada linkedin.com/jobs/view que Carlos te pase. "
            "No inventes vacantes de LinkedIn. Get on Board, Remotive y RemoteOK sí listan vacantes. "
            "(2) Muestra a Carlos cada oferta con ref, empresa, rol, fuente, ubicación y URL. "
            "Marca already_saved. (3) ESPERA autorización explícita (L1 y L3, todas, todas menos L2). "
            "(4) save_job_listings({refs: ['L1','L3']}) crea vacancies con evaluation=pending_review "
            "para seguimiento en Vacantes. Si Carlos pega una URL concreta, importar y guardar esa ref "
            "en el mismo turno sí está autorizado. Nunca uses create_career_record para esto."
        ),
        default_model_id="us.anthropic.claude-haiku-4-5-20251001-v1:0",
    ),
    "digital": AgentProfile(
        id="digital",
        label="Presencia Digital",
        domain_keys=["digital"],
        resource_keys=_DIGITAL_RESOURCES,
        methodology_sections=["Presencia Digital"],
        system_prompt_suffix=(
            "Especialista en presencia digital, publicaciones del portal y LinkedIn. "
            "Publica ahora, programa o elimina posts programados según pida el usuario."
        ),
        default_model_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    ),
    "networking": AgentProfile(
        id="networking",
        label="Networking",
        domain_keys=["networking"],
        resource_keys=["contact-interactions", "networking-activities"],
        methodology_sections=["Networking"],
        system_prompt_suffix="Especialista en contactos y seguimiento de networking.",
        default_model_id="us.anthropic.claude-haiku-4-5-20251001-v1:0",
    ),
    "support": AgentProfile(
        id="support",
        label="Soporte",
        domain_keys=["support"],
        resource_keys=["tags"],
        methodology_sections=["Soporte"],
        system_prompt_suffix="Especialista en taxonomía y tags.",
        default_model_id="us.anthropic.claude-haiku-4-5-20251001-v1:0",
    ),
    "methodologies": AgentProfile(
        id="methodologies",
        label="Metodologías",
        domain_keys=["meta"],
        resource_keys=["operational-methodologies"],
        methodology_sections=[],
        system_prompt_suffix="Guardián de metodologías operativas del sistema.",
        default_model_id="cohere.command-r-v1:0",
    ),
    "pdf_design": AgentProfile(
        id="pdf_design",
        label="Diseño PDF",
        domain_keys=["document_output"],
        resource_keys=["pdf-output-templates", "pdf-template-styles"],
        methodology_sections=["Diseño PDF"],
        system_prompt_suffix=_PDF_DESIGN_SUFFIX,
        default_model_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        allowed_tool_names={
            "search_knowledge_base",
            "pdf_template",
            "pdf_style",
            "generate_pdf",
            "describe_resource_schema",
        },
    ),
    "visual_design": AgentProfile(
        id="visual_design",
        label="Agente Visual",
        domain_keys=["visual_media"],
        resource_keys=None,
        methodology_sections=["Diseño Visual"],
        system_prompt_suffix=(
            "Generas imágenes para publicaciones, LinkedIn y proyectos. "
            "Paleta cyan #0891B2, estilo profesional/tecnológico."
        ),
        default_model_id="amazon.nova-lite-v1:0",
        allowed_tool_names={
            "generate_image",
            "attach_image_to_record",
            "list_generated_images",
            "search_knowledge_base",
            "update_career_record",
        },
    ),
}

# ============================================================================
# Mapas de enrutamiento
# ============================================================================

_ROUTE_TO_PROFILE = {
    "/linkedin": "digital",
    "/job-discovery": "search",
    "/career/publications": "digital",
    "/career/operational-methodologies": "methodologies",
    "/agent/chat": "orchestrator",
    "/agent/pdf-templates": "pdf_design",
    "/agent/pdf-template-styles": "pdf_design",
}

_RESOURCE_TO_DOMAIN = {
    **{k: "identity" for k in _IDENTITY_RESOURCES},
    **{k: "search" for k in _SEARCH_RESOURCES},
    **{k: "digital" for k in _DIGITAL_RESOURCES},
    "contact-interactions": "networking",
    "networking-activities": "networking",
    "tags": "support",
    "operational-methodologies": "methodologies",
}

_DOMAIN_TO_PROFILE = {
    "identity": "identity",
    "search": "search",
    "digital": "digital",
    "networking": "networking",
    "support": "support",
}


# ============================================================================
# Resolución de perfil y tools
# ============================================================================

def get_profile(profile_id: str) -> AgentProfile:
    if profile_id not in _PROFILES:
        raise KeyError(f"Unknown agent profile: {profile_id}")
    return _PROFILES[profile_id]


def list_profiles() -> List[AgentProfile]:
    return list(_PROFILES.values())


def resolve_agent_profile(
    *,
    chat_surface: str,
    agent_profile_id: Optional[str],
    page_context: Optional[dict],
) -> AgentProfile:
    """Router: chat general → orquestador; contextual → ruta/recurso."""
    if chat_surface == "general":
        return get_profile("orchestrator")
    if agent_profile_id:
        return get_profile(agent_profile_id)
    if page_context:
        route = page_context.get("route") or ""
        if route in _ROUTE_TO_PROFILE:
            return get_profile(_ROUTE_TO_PROFILE[route])
        rk = page_context.get("resource_key")
        if rk and rk in _RESOURCE_TO_DOMAIN:
            return get_profile(_DOMAIN_TO_PROFILE[_RESOURCE_TO_DOMAIN[rk]])
    return get_profile("orchestrator")


def tools_for_profile(profile: AgentProfile, all_tool_names: Set[str]) -> Set[str]:
    """Filtra nombres de tool según perfil."""
    if profile.id == "orchestrator":
        names = set(all_tool_names)
        if profile.can_delegate:
            names.add("delegate_to_specialist")
        return names
    if profile.allowed_tool_names is not None:
        return profile.allowed_tool_names & all_tool_names
    names = set(_BUILTIN_TOOL_NAMES) - {"delegate_to_specialist"}
    if profile.id != "digital":
        names -= {
            "get_linkedin_status",
            "list_linkedin_posts",
            "create_linkedin_post",
            "delete_scheduled_linkedin_post",
        }
    if profile.id not in ("pdf_design", "search", "orchestrator"):
        names -= {
            "pdf_template",
            "pdf_style",
            "generate_pdf",
        }
    if profile.id != "visual_design":
        names -= {"generate_image", "attach_image_to_record", "list_generated_images"}
    if profile.id != "search":
        names -= {
            "list_job_providers",
            "run_job_discovery",
            "import_job_url",
            "save_job_listings",
        }
    return names
