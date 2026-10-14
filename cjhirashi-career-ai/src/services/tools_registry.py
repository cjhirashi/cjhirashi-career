"""
Catálogo de tools Converse del harness: esquemas, alcance y resolución de herramientas efectivas.

Traslado de `cjhirashi-career-api/src/services/bedrock/tools.py` (esquemas) y `profile_tools.py`
(set efectivo), sin ejecución: los ejecutores y el acceso a datos por REST son del Bloque F.
`search_knowledge_base` se retira (D-15): la memoria es FTS en Postgres y las metodologías
se leen con `list_career_record` / `get_career_record` sobre `operational-methodologies`.
"""
from typing import Any, Dict, List, Optional, Sequence, Set

from providers.base import ToolSpec
from services.agent_profiles import AgentProfile, delegate_tool_description, tools_for_profile

# ============================================================================
# Parámetros compartidos de schemas
# ============================================================================

_RESOURCE_KEY_PARAM = {
    "type": "string",
    "description": "resource_key, ej. vacancies, publications, projects",
}

_RECORD_ID_PARAM = {
    "type": "string",
    "description": "ID prefijado del registro, ej. ach-17, cmp-42, vac-7. Usar el id completo.",
}

# ============================================================================


# Schemas Converse (toolSpec.inputSchema.json)
_RAW_TOOLS: List[Dict[str, Any]] = [
    {"name": "list_recent_changes", "description": "Bitácora reciente del agente.", "schema": {"type": "object", "properties": {"resource_key": {"type": "string"}, "limit": {"type": "integer"}}}},
    {"name": "restore_deleted_record", "description": "Restaura un delete desde audit_id.", "schema": {"type": "object", "properties": {"audit_id": {"type": "integer"}}, "required": ["audit_id"]}},
    {"name": "describe_resource_schema", "description": "Campos válidos de un resource_key.", "schema": {"type": "object", "properties": {"resource_key": _RESOURCE_KEY_PARAM}, "required": ["resource_key"]}},
    {"name": "list_career_record", "description": "Lista registros paginados (vista compacta: id, title, summary). Para 'lista todos mis X' usa limit=100 sin search. Incluye TODOS los items; revisa total_count y pagina si has_more. Si necesitas revisar una columna puntual (ej. nivel, category) en TODOS los registros de un resource_key, pasa fields=['esa_columna'] aquí en vez de llamar get_career_record uno por uno — un solo list_career_record con fields trae esa columna en cada item de la página.", "schema": {"type": "object", "properties": {"resource_key": _RESOURCE_KEY_PARAM, "search": {"type": "string"}, "limit": {"type": "integer"}, "skip": {"type": "integer"}, "fields": {"type": "array", "items": {"type": "string"}, "description": "Opcional. Columnas extra a incluir en cada item de la lista, además de id/title/summary."}}, "required": ["resource_key"]}},
    {"name": "count_career_records", "description": "Cuenta registros de un resource_key. Usar para '¿cuántos X tengo?'.", "schema": {"type": "object", "properties": {"resource_key": _RESOURCE_KEY_PARAM, "search": {"type": "string"}}, "required": ["resource_key"]}},
    {"name": "get_career_record", "description": "Obtiene un registro por id. En registros grandes (p.ej. projects, cv-versions) pasa 'fields' con solo las columnas que necesitas para no traer todo el registro; el id siempre se incluye. Si no sabes los nombres exactos, usa describe_resource_schema primero.", "schema": {"type": "object", "properties": {"resource_key": _RESOURCE_KEY_PARAM, "record_id": _RECORD_ID_PARAM, "fields": {"type": "array", "items": {"type": "string"}, "description": "Opcional. Columnas a devolver (id siempre incluido)."}}, "required": ["resource_key", "record_id"]}},
    {"name": "create_career_record", "description": "Crea registro. Escribir el contenido en el chat NO guarda: llama esta tool con resource_key y fields.", "schema": {"type": "object", "properties": {"resource_key": _RESOURCE_KEY_PARAM, "fields": {"type": "object"}}, "required": ["resource_key", "fields"]}},
    {"name": "update_career_record", "description": "Actualiza registro. Escribir el contenido en el chat NO guarda: llama esta tool con resource_key, record_id y fields.", "schema": {"type": "object", "properties": {"resource_key": _RESOURCE_KEY_PARAM, "record_id": _RECORD_ID_PARAM, "fields": {"type": "object"}}, "required": ["resource_key", "record_id", "fields"]}},
    {
        "name": "bulk_update_career_record",
        "description": (
            "Actualiza VARIOS registros del mismo resource_key en una sola llamada "
            "(ej. reclasificar todas las competencias en 4 categorías). Úsala en vez de "
            "llamar update_career_record una por una cuando el cambio toca varias filas. "
            "updates es una lista de {record_id, fields}; máximo 200 por llamada, pero si son "
            "más de ~25-30 registros o los fields llevan texto largo, mándalos en varias "
            "llamadas de ~20-25 items cada una (una tras otra, en el mismo turno) en vez de un "
            "solo payload gigante — evita cortes por límite de tokens de salida a mitad de la "
            "respuesta. Escribirlo en el chat NO guarda nada — llama esta tool."
        ),
        "schema": {
            "type": "object",
            "properties": {
                "resource_key": _RESOURCE_KEY_PARAM,
                "updates": {
                    "type": "array",
                    "description": "Cada item: {record_id, fields}. fields son las columnas a cambiar en ese registro.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "record_id": _RECORD_ID_PARAM,
                            "fields": {"type": "object"},
                        },
                        "required": ["record_id", "fields"],
                    },
                },
            },
            "required": ["resource_key", "updates"],
        },
    },
    {"name": "delete_career_record", "description": "Elimina registro.", "schema": {"type": "object", "properties": {"resource_key": _RESOURCE_KEY_PARAM, "record_id": _RECORD_ID_PARAM}, "required": ["resource_key", "record_id"]}},
    {"name": "get_linkedin_status", "description": "Estado conexión LinkedIn.", "schema": {"type": "object", "properties": {}}},
    {"name": "list_linkedin_posts", "description": "Cola e historial posts LinkedIn.", "schema": {"type": "object", "properties": {"limit": {"type": "integer"}}}},
    {"name": "create_linkedin_post", "description": "Publicar ahora (sin scheduled_at) o programar (ISO futuro).", "schema": {"type": "object", "properties": {"text": {"type": "string"}, "image_url": {"type": "string"}, "scheduled_at": {"type": "string"}}, "required": ["text"]}},
    {"name": "delete_scheduled_linkedin_post", "description": "Elimina post status=scheduled.", "schema": {"type": "object", "properties": {"post_id": {"type": "string", "description": "ID prefijado, ej. lnp-3"}}, "required": ["post_id"]}},
    {"name": "pdf_template", "description": "CRUD de pdf_output_templates (HTML, IDs pdt-N). No edita CSS. action=list|get|create|update. create requiere slug, document_type, title, html_template. update requiere template_id y los campos a cambiar (html_template, style_id, variables, …) en el nivel superior o en fields. Escribir HTML en el chat NO guarda.", "schema": {"type": "object", "properties": {"action": {"type": "string", "enum": ["list", "get", "create", "update"]}, "template_id": {"type": "string", "description": "ID prefijado, ej. pdt-1"}, "slug": {"type": "string"}, "document_type": {"type": "string"}, "title": {"type": "string"}, "html_template": {"type": "string"}, "style_id": {"type": "string", "description": "ID del estilo CSS, ej. pds-1"}, "variables": {"type": "string"}, "default_only": {"type": "boolean"}, "fields": {"type": "object", "description": "Opcional en update; también se aceptan html_template/style_id/variables en el nivel superior"}}, "required": ["action"]}},
    {"name": "pdf_style", "description": "CRUD de pdf_template_styles (CSS reutilizable, IDs pds-N). No edita HTML. action=list|get|create|update. create requiere slug, title, css_content. update requiere style_id y al menos un campo (style_guide, css_content, title, …) en el nivel superior o en fields. Escribir Markdown en el chat NO guarda style_guide.", "schema": {"type": "object", "properties": {"action": {"type": "string", "enum": ["list", "get", "create", "update"]}, "style_id": {"type": "string", "description": "ID prefijado, ej. pds-1"}, "slug": {"type": "string"}, "title": {"type": "string"}, "css_content": {"type": "string"}, "style_guide": {"type": "string", "description": "Markdown de clases/etiquetas. En update puede ir aquí (nivel superior) o en fields.style_guide"}, "description": {"type": "string"}, "fields": {"type": "object", "description": "Opcional en update; también se acepta style_guide/css_content en el nivel superior"}}, "required": ["action"]}},
    {"name": "generate_pdf", "description": "Genera PDF desde plantilla HTML (template_id) con variables. Preview de diseño, no a partir de un registro de carrera.", "schema": {"type": "object", "properties": {"template_id": {"type": "string", "description": "ID prefijado, ej. pdt-1"}, "variables": {"type": "object"}, "title": {"type": "string"}}, "required": ["template_id"]}},
    {"name": "list_pdf_capable_resources", "description": "Tablas que pueden emitir PDF (cv-versions, cover-letter-versions) y cómo mapear campos al template.", "schema": {"type": "object", "properties": {}}},
    {"name": "render_record_pdf", "description": "Genera el PDF de un registro con función PDF. resource_key + record_id; template_id opcional (si falta, plantilla default del document_type).", "schema": {"type": "object", "properties": {"resource_key": {"type": "string", "description": "cv-versions o cover-letter-versions"}, "record_id": _RECORD_ID_PARAM, "template_id": {"type": "string", "description": "Opcional, ej. pdt-1"}, "title": {"type": "string"}}, "required": ["resource_key", "record_id"]}},
    {
        "name": "generate_image",
        "description": (
            "Pide el prompt al solicitante y genera una imagen IA para agentes/proyectos/publicaciones. "
            "Ajusta y sube a MinIO en la carpeta de purpose ya en la medida exacta (500x500 agentes, "
            "1920x1080 proyectos/publicaciones), PNG comprimido para web. name opcional (si falta, se deriva del prompt)."
        ),
        "schema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string"},
                "purpose": {"type": "string", "enum": ["agentes", "proyectos", "publicaciones"]},
                "name": {"type": "string", "description": "Nombre legible para el archivo (opcional)"},
            },
            "required": ["prompt", "purpose"],
        },
    },
    {
        "name": "store_uploaded_image",
        "description": (
            "Cuando el solicitante YA tiene una imagen (adjunta en el chat, file_id) y solo quiere optimizarla "
            "y guardarla — sin generar nada nuevo. Ajusta a la medida exacta del purpose y sube a MinIO igual "
            "que generate_image, devolviendo el link."
        ),
        "schema": {
            "type": "object",
            "properties": {
                "source_file_id": {"type": "string", "description": "file_id del adjunto ya subido"},
                "purpose": {"type": "string", "enum": ["agentes", "proyectos", "publicaciones"]},
                "name": {"type": "string", "description": "Nombre legible para el archivo (opcional)"},
            },
            "required": ["source_file_id", "purpose"],
        },
    },
    {
        "name": "attach_image_to_record",
        "description": "Pone image_url en publications, projects, o la foto de un agente del catálogo (resource_key=agent-profile, record_id=id del perfil).",
        "schema": {
            "type": "object",
            "properties": {
                "resource_key": {"type": "string", "enum": ["publications", "projects", "agent-profile"]},
                "record_id": _RECORD_ID_PARAM,
                "image_url": {"type": "string"},
            },
            "required": ["resource_key", "record_id", "image_url"],
        },
    },
    {
        "name": "list_generated_images",
        "description": "Lista imágenes generadas/guardadas por el agente Visual (agentes/proyectos/publicaciones). purpose opcional filtra una sola sección.",
        "schema": {
            "type": "object",
            "properties": {
                "purpose": {"type": "string", "enum": ["agentes", "proyectos", "publicaciones"]},
                "limit": {"type": "integer"},
            },
        },
    },
    {"name": "delegate_to_specialist", "description": "Delega a un especialista de nivel inferior (L1→L2|L3, L2→L3). Nunca hacia arriba.", "schema": {"type": "object", "properties": {"agent_profile_id": {"type": "string"}, "task": {"type": "string"}, "context": {"type": "string"}}, "required": ["agent_profile_id", "task"]}},
    {"name": "list_job_providers", "description": "Portales de vacantes habilitados (indeed, linkedin, getonboard, remotive, remoteok, company_boards).", "schema": {"type": "object", "properties": {}}},
    {
        "name": "run_job_discovery",
        "description": (
            "Busca vacantes y devuelve un PREVIEW con refs L1, L2… No crea registros. "
            "providers: indeed (vía Adzuna), linkedin (solo URLs oficiales de búsqueda; no inventes vacantes), "
            "getonboard, remotive, remoteok. Presenta la lista a Carlos y ESPERA a que autorice refs concretas "
            "antes de save_job_listings."
        ),
        "schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "location": {"type": "string"},
                "providers": {"type": "array", "items": {"type": "string"}},
                "target_role_id": {"type": "string", "description": "ID prefijado del rol objetivo, ej. trl-2"},
                "include_company_boards": {"type": "boolean"},
                "remote": {"type": "boolean"},
            },
        },
    },
    {
        "name": "import_job_url",
        "description": (
            "Importa UNA vacante concreta por URL (linkedin.com/jobs/view/..., Indeed, OCC) al preview "
            "con una ref nueva. Si Carlos pegó la URL, eso autoriza guardar esa ref."
        ),
        "schema": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]},
    },
    {
        "name": "save_job_listings",
        "description": (
            "Crea vacancies con evaluation=pending_review SOLO de refs (L1, L3…) que Carlos autorizó "
            "de la última búsqueda o import. Prohibido llamar sin autorización explícita. "
            "No inventes refs ni pases listings inventados. Omite search_url."
        ),
        "schema": {
            "type": "object",
            "properties": {
                "refs": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Refs autorizadas, p.ej. ['L1','L3']",
                },
                "target_role_id": {"type": "string", "description": "ID prefijado del rol objetivo, ej. trl-2"},
            },
            "required": ["refs"],
        },
    },
    {"name": "web_search", "description": "Busca en internet. Devuelve títulos, URLs y snippets. No inventes fuentes.", "schema": {"type": "object", "properties": {"query": {"type": "string"}, "max_results": {"type": "integer"}}, "required": ["query"]}},
    {"name": "web_fetch", "description": "Lee el texto de una URL http/https pública. Bloquea redes privadas. No uses URLs inventadas.", "schema": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}},
    {"name": "get_github_status", "description": "Estado de la conexión GitHub (GITHUB_TOKEN).", "schema": {"type": "object", "properties": {}}},
    {"name": "list_github_repos", "description": "Lista repos del usuario autenticado o de un owner. query filtra por nombre/descripcion.", "schema": {"type": "object", "properties": {"owner": {"type": "string"}, "query": {"type": "string"}, "per_page": {"type": "integer"}}}},
    {"name": "get_github_repo", "description": "Metadatos de un repo. owner opcional; repo acepta 'owner/name'.", "schema": {"type": "object", "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}}, "required": ["repo"]}},
    {"name": "list_github_contents", "description": "Lista archivos/carpetas de un repo. path vacío = raíz.", "schema": {"type": "object", "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}, "path": {"type": "string"}, "ref": {"type": "string"}}, "required": ["repo"]}},
    {"name": "get_github_file", "description": "Lee el contenido de un archivo de un repo (texto, truncado).", "schema": {"type": "object", "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}, "path": {"type": "string"}, "ref": {"type": "string"}}, "required": ["repo", "path"]}},
    {"name": "search_github_code", "description": "Busca código en repos del usuario. Requiere GITHUB_TOKEN.", "schema": {"type": "object", "properties": {"query": {"type": "string"}, "owner": {"type": "string"}, "repo": {"type": "string"}}, "required": ["query"]}},
    {
        "name": "agent_catalog_settings",
        "description": "Catálogo de agentes: prompt suffix, destinos de delegación y metodologías asignadas por perfil. action=list|get|update_prompt|update_delegation|update_methodologies. profile_id requerido salvo list.",
        "schema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["list", "get", "update_prompt", "update_delegation", "update_methodologies"]},
                "profile_id": {"type": "string", "description": "Nombre de sistema (agent_professional_identity) o record id (agent-2)"},
                "system_prompt_suffix": {"type": "string", "description": "update_prompt: null/omitido restaura el default del código"},
                "target_ids": {"type": "array", "items": {"type": "string"}, "description": "update_delegation: destinos permitidos; [] = no delega a nadie; omitido restaura el default por nivel"},
                "methodology_ids": {"type": "array", "items": {"type": "string"}, "description": "update_methodologies: IDs opm-N que este agente debe consultar"},
            },
            "required": ["action"],
        },
    },
    {
        "name": "admin_section_settings",
        "description": (
            "Secciones del Admin: qué agente L2 atiende el chat contextual de cada "
            "pantalla Y los textos de instrucción del sidebar por vista. "
            "action=list|get|update. section_id es el PK sec-N (p.ej. sec-1); "
            "mira action=list, campo id. El campo system_name (dashboard, career-projects…) "
            "es solo el nombre legible. section_id requerido salvo en list. En update, "
            "`views` escribe sidebar_title/sidebar_body por clave de vista (main/list/view/edit); "
            "null o \"\" en un subcampo restaura el texto de código."
        ),
        "schema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["list", "get", "update"]},
                "section_id": {"type": "string", "description": "PK de la sección, p.ej. sec-1 (NO el system_name)"},
                "agent_profile_id": {"type": "string", "description": "Agente L2 del chat contextual del sidebar; string vacío restaura el default del código; debe ser un agente de nivel 2"},
                "views": {
                    "type": "object",
                    "description": (
                        "update: { <view_key>: { sidebar_title?, sidebar_body? } }. "
                        "view_key ∈ main|list|view|edit según la sección. null/\"\" restaura código."
                    ),
                    "additionalProperties": {
                        "type": "object",
                        "properties": {
                            "sidebar_title": {"type": ["string", "null"]},
                            "sidebar_body": {"type": ["string", "null"]},
                        },
                    },
                },
            },
            "required": ["action"],
        },
    },
    {
        "name": "bedrock_global_settings",
        "description": "Prompts globales que aplican a TODOS los agentes (system prompt base + reglas de grounding/metodologías). action=get|update_system_prompt|update_global_rules.",
        "schema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["get", "update_system_prompt", "update_global_rules"]},
                "text": {"type": "string", "description": "null/omitido restaura el default del código"},
            },
            "required": ["action"],
        },
    },
    {
        "name": "error_report_settings",
        "description": "Reportes de falla del sistema (tabla error_reports, IDs err-N). action=list|get|resolve|reopen|summary. list acepta resolved(bool), severity(warning|error|critical), limit. get/resolve/reopen requieren report_id. resolve acepta resolution_notes. Marcar resuelto = el problema ya se corrigió en el sistema.",
        "schema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["list", "get", "resolve", "reopen", "summary"]},
                "report_id": {"type": "string", "description": "ID prefijado, ej. err-3"},
                "resolved": {"type": "boolean", "description": "list: filtra por estado (false = pendientes)"},
                "severity": {"type": "string", "enum": ["warning", "error", "critical"]},
                "limit": {"type": "integer"},
                "resolution_notes": {"type": "string", "description": "resolve: qué se hizo para resolver"},
            },
            "required": ["action"],
        },
    },
]


_WRITE_TOOLS = {
    "create_career_record",
    "update_career_record",
    "bulk_update_career_record",
    "delete_career_record",
    "create_linkedin_post",
    "pdf_template",
    "pdf_style",
    "generate_pdf",
    "render_record_pdf",
    "generate_image",
    "store_uploaded_image",
    "attach_image_to_record",
    "save_job_listings",
    "agent_catalog_settings",
    "admin_section_settings",
    "bedrock_global_settings",
    "error_report_settings",
}


WRITE_TOOLS = _WRITE_TOOLS

# ============================================================================
# Catálogo y alcance
# ============================================================================


def all_tool_names() -> Set[str]:
    return {t["name"] for t in _RAW_TOOLS}


# spec 004 · RF-010/011 — clasificación de cada tool:
#   "section" -> opera los datos de una sección; sólo llega a un agente vía la sección.
#   "agent"   -> gestionada por nivel (delegación).
#   "both"    -> útil por sección y directa (default).
_TOOL_SCOPES: Dict[str, str] = {
    "list_career_record": "section",
    "get_career_record": "section",
    "create_career_record": "section",
    "update_career_record": "section",
    "delete_career_record": "section",
    "bulk_update_career_record": "section",
    "count_career_records": "section",
    "describe_resource_schema": "section",
    "delegate_to_specialist": "agent",
}


def tool_scope(name: str) -> str:
    """`section` | `agent` | `both` (default) para una tool integrada."""
    return _TOOL_SCOPES.get(name, "both")


def tool_specs(
    allowed: Optional[Set[str]] = None,
    *,
    caller_profile: Optional[AgentProfile] = None,
    delegate_ids: Optional[List[str]] = None,
) -> List[ToolSpec]:
    """Definiciones de tool para el proveedor (neutras: `ToolSpec`)."""
    specs: List[ToolSpec] = []
    for t in _RAW_TOOLS:
        if allowed is not None and t["name"] not in allowed:
            continue
        description = t["description"]
        if t["name"] == "delegate_to_specialist" and caller_profile is not None:
            description = delegate_tool_description(caller_profile, target_ids=delegate_ids)
        specs.append(ToolSpec(name=t["name"], description=description, input_schema=t["schema"]))
    return specs


def list_builtin_tool_catalog() -> List[Dict[str, str]]:
    """Catálogo read-only de tools integradas (name + description + scope) — RF-009/010."""
    return [
        {"name": t["name"], "description": t["description"], "scope": tool_scope(t["name"])}
        for t in _RAW_TOOLS
    ]


# ============================================================================
# Herramientas efectivas por perfil (código por defecto, override Admin, secciones L2)
# ============================================================================


def default_tool_names(profile: AgentProfile) -> Set[str]:
    """Set por defecto derivado del código (nivel + allowed_tool_names)."""
    return set(tools_for_profile(profile, all_tool_names()))


def effective_tool_names(
    profile: AgentProfile,
    override: Optional[Sequence[str]],
    *,
    section_tools: Optional[Set[str]] = None,
) -> Set[str]:
    """Set efectivo de herramientas para un turno.

    - L2 con `section_tools` (unión de sus secciones): ese es el set base (sin override directo).
    - L1/L3: `override` reemplaza el default de código; `None` = default.
    - `delegate_to_specialist` se aplica siempre por nivel (D-2).
    """
    if section_tools is not None and profile.level == 2:
        names = set(section_tools) & all_tool_names()
    elif override is None:
        names = default_tool_names(profile)
    else:
        names = set(override) & all_tool_names()
    if profile.can_delegate:
        names.add("delegate_to_specialist")
    else:
        names.discard("delegate_to_specialist")
    return names


def validate_tool_names(tool_names: Sequence[str]) -> List[str]:
    """Normaliza (ordenado, sin duplicados) y valida contra el catálogo.

    `ValueError` si algún nombre no existe o si es de `scope == "section"`: esas sólo llegan
    a un agente vía su sección, no se asignan directo a L1/L3 (spec 004 RF-011).
    """
    cleaned = sorted(set(tool_names))
    unknown = set(cleaned) - all_tool_names()
    if unknown:
        raise ValueError(f"Unknown tool names: {sorted(unknown)}")
    section_only = sorted(t for t in cleaned if tool_scope(t) == "section")
    if section_only:
        raise ValueError(
            f"Tools de sección no asignables directo a un agente: {section_only}. "
            "Se reciben ligando el agente a la sección."
        )
    return cleaned
