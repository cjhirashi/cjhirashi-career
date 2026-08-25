"""
Tools Converse — schemas y ejecución (CRUD, LinkedIn, PDF, imágenes, web, GitHub).

Tier 1: career CRUD (delegado a bedrock_service._execute_tool).
Tier 2: LinkedIn, plantillas PDF, estilos CSS, imágenes, vacantes, consulta web, GitHub, delegación.
Ver api/docs/BEDROCK-HARNESS.md.
"""
import io
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from sqlalchemy import desc, select

from config import settings
from models.linkedin_connection import LinkedInConnection
from models.linkedin_post import LinkedInPost, LinkedInPostStatus
from models.pdf_output_template import PdfOutputTemplate
from models.pdf_template_style import PdfTemplateStyle
from repositories.career_repository import CareerRepository
from services import bedrock_service, storage_service
from services.id_generator import normalize_prefixed_id
from services.bedrock.errors import BedrockError
from services.bedrock.tool_results import truncate_tool_result

_PDF_STYLE_REPO = CareerRepository(PdfTemplateStyle, resource_key="pdf-template-styles", vectorize=False)
_PDF_STYLE_UPDATE_FIELDS = {"slug", "title", "description", "css_content", "style_guide", "is_active"}


def merge_writable_fields(tool_input: Dict[str, Any], allowed: Set[str]) -> Dict[str, Any]:
    """Collect writable keys from nested `fields` and the top level.

    Create uses top-level properties (`style_guide`, `css_content`, …). Models
    often update the same way; requiring a nested `fields` object dropped the
    payload and the agent then claimed success in chat without writing.
    Top-level values override nested ones when both are present.
    """
    merged: Dict[str, Any] = {}
    nested = tool_input.get("fields")
    if isinstance(nested, dict):
        for key, value in nested.items():
            if key in allowed:
                merged[key] = value
    for key in allowed:
        if key in tool_input and tool_input[key] is not None:
            merged[key] = tool_input[key]
    return merged

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
# Schemas de tools Converse
# ============================================================================

# Schemas Converse (toolSpec.inputSchema.json)
_RAW_TOOLS: List[Dict[str, Any]] = [
    {"name": "list_recent_changes", "description": "Bitácora reciente del agente.", "schema": {"type": "object", "properties": {"resource_key": {"type": "string"}, "limit": {"type": "integer"}}}},
    {"name": "restore_deleted_record", "description": "Restaura un delete desde audit_id.", "schema": {"type": "object", "properties": {"audit_id": {"type": "integer"}}, "required": ["audit_id"]}},
    {"name": "describe_resource_schema", "description": "Campos válidos de un resource_key.", "schema": {"type": "object", "properties": {"resource_key": _RESOURCE_KEY_PARAM}, "required": ["resource_key"]}},
    {"name": "search_knowledge_base", "description": "Búsqueda semántica Qdrant por significado. NO usar para 'lista todos mis X' — usa list_career_record.", "schema": {"type": "object", "properties": {"query": {"type": "string"}, "top_k": {"type": "integer"}, "type": {"type": "string", "enum": ["methodology", "career_record"]}}, "required": ["query"]}},
    {"name": "list_career_record", "description": "Lista registros paginados. Para 'lista todos mis X' usa limit=100 sin search (no search_knowledge_base). Incluye TODOS los items; revisa total_count y pagina si has_more.", "schema": {"type": "object", "properties": {"resource_key": _RESOURCE_KEY_PARAM, "search": {"type": "string"}, "limit": {"type": "integer"}, "skip": {"type": "integer"}}, "required": ["resource_key"]}},
    {"name": "count_career_records", "description": "Cuenta registros de un resource_key. Usar para '¿cuántos X tengo?'.", "schema": {"type": "object", "properties": {"resource_key": _RESOURCE_KEY_PARAM, "search": {"type": "string"}}, "required": ["resource_key"]}},
    {"name": "get_career_record", "description": "Obtiene un registro por id.", "schema": {"type": "object", "properties": {"resource_key": _RESOURCE_KEY_PARAM, "record_id": _RECORD_ID_PARAM}, "required": ["resource_key", "record_id"]}},
    {"name": "create_career_record", "description": "Crea registro. Escribir el contenido en el chat NO guarda: llama esta tool con resource_key y fields.", "schema": {"type": "object", "properties": {"resource_key": _RESOURCE_KEY_PARAM, "fields": {"type": "object"}}, "required": ["resource_key", "fields"]}},
    {"name": "update_career_record", "description": "Actualiza registro. Escribir el contenido en el chat NO guarda: llama esta tool con resource_key, record_id y fields.", "schema": {"type": "object", "properties": {"resource_key": _RESOURCE_KEY_PARAM, "record_id": _RECORD_ID_PARAM, "fields": {"type": "object"}}, "required": ["resource_key", "record_id", "fields"]}},
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
    {"name": "generate_image", "description": "Genera imagen IA y sube a MinIO.", "schema": {"type": "object", "properties": {"prompt": {"type": "string"}, "purpose": {"type": "string"}, "width": {"type": "integer"}, "height": {"type": "integer"}}, "required": ["prompt"]}},
    {"name": "attach_image_to_record", "description": "Pone image_url en publications o projects.", "schema": {"type": "object", "properties": {"resource_key": {"type": "string"}, "record_id": _RECORD_ID_PARAM, "image_url": {"type": "string"}}, "required": ["resource_key", "record_id", "image_url"]}},
    {"name": "list_generated_images", "description": "Lista imágenes ai-generated.", "schema": {"type": "object", "properties": {"limit": {"type": "integer"}}}},
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
]

_WRITE_TOOLS = {
    "create_career_record",
    "update_career_record",
    "delete_career_record",
    "create_linkedin_post",
    "pdf_template",
    "pdf_style",
    "generate_pdf",
    "render_record_pdf",
    "generate_image",
    "attach_image_to_record",
    "save_job_listings",
}

_PDF_TEMPLATE_ALIASES = {
    "list_pdf_templates": "list",
    "get_pdf_template": "get",
    "create_pdf_template": "create",
    "update_pdf_template": "update",
}

_PDF_STYLE_ALIASES = {
    "list_pdf_template_styles": "list",
    "get_pdf_template_style": "get",
    "create_pdf_template_style": "create",
    "update_pdf_template_style": "update",
}

_PDF_TEMPLATE_UPDATE_FIELDS = {
    "slug",
    "document_type",
    "title",
    "description",
    "html_template",
    "style_id",
    "variables",
    "variables_schema",
    "preview_notes",
    "is_active",
    "is_default",
}

# Tablas de carrera con función PDF (L3 agent_pdf_render).
PDF_CAPABLE_RESOURCES = {
    "cv-versions": {
        "document_type": "cv",
        "content_attr": "content",
        "title_attr": "title",
    },
    "cover-letter-versions": {
        "document_type": "cover_letter",
        "content_attr": "body_content",
        "title_attr": "title",
    },
}

_LEGACY = {
    "list_recent_changes", "restore_deleted_record", "describe_resource_schema", "search_knowledge_base",
    "list_career_record", "count_career_records", "get_career_record", "create_career_record", "update_career_record", "delete_career_record",
}


# ============================================================================
# Especificaciones Converse
# ============================================================================

def all_tool_names() -> Set[str]:
    return {t["name"] for t in _RAW_TOOLS}


def converse_tool_specs(allowed: Optional[Set[str]] = None, *, caller_profile=None) -> List[Dict[str, Any]]:
    """Convierte definiciones a formato toolConfig.tools de Converse API."""
    specs = []
    for t in _RAW_TOOLS:
        if allowed is not None and t["name"] not in allowed:
            continue
        description = t["description"]
        if t["name"] == "delegate_to_specialist" and caller_profile is not None:
            from services.bedrock.agent_profiles import delegate_tool_description
            description = delegate_tool_description(caller_profile)
        specs.append({
            "toolSpec": {
                "name": t["name"],
                "description": description,
                "inputSchema": {"json": t["schema"]},
            }
        })
    return specs


# ============================================================================
# Tools de integración
# ============================================================================

async def _linkedin_connection(db, user_id: str) -> Optional[LinkedInConnection]:
    result = await db.execute(select(LinkedInConnection).where(LinkedInConnection.user_id == user_id))
    conn = result.scalar_one_or_none()
    if conn and conn.expires_at > datetime.now(timezone.utc):
        return conn
    return None


async def _run_pdf_template(db, user_id: str, action: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    """CRUD de pdf_output_templates (HTML)."""
    if action == "list":
        q = select(PdfOutputTemplate).where(PdfOutputTemplate.user_id == user_id, PdfOutputTemplate.is_active.is_(True))
        if tool_input.get("document_type"):
            q = q.where(PdfOutputTemplate.document_type == tool_input["document_type"])
        result = await db.execute(q.order_by(PdfOutputTemplate.title))
        rows = result.scalars().all()
        return {
            "items": [
                {
                    "id": r.id,
                    "slug": r.slug,
                    "document_type": r.document_type,
                    "title": r.title,
                    "style_id": r.style_id,
                    "is_default": r.is_default,
                }
                for r in rows
            ]
        }

    if action == "get":
        q = select(PdfOutputTemplate).where(PdfOutputTemplate.user_id == user_id, PdfOutputTemplate.is_active.is_(True))
        if tool_input.get("template_id"):
            template_id = normalize_prefixed_id("pdf_output_templates", tool_input["template_id"])
            q = q.where(PdfOutputTemplate.id == template_id)
        elif tool_input.get("slug"):
            q = q.where(PdfOutputTemplate.slug == tool_input["slug"])
        elif tool_input.get("default_only") and tool_input.get("document_type"):
            q = q.where(
                PdfOutputTemplate.document_type == tool_input["document_type"],
                PdfOutputTemplate.is_default.is_(True),
            )
        else:
            return {"error": "specify template_id, slug, or default_only+document_type"}
        result = await db.execute(q.limit(1))
        row = result.scalar_one_or_none()
        if not row:
            return {"error": "not_found"}
        return {
            "item": {
                "id": row.id,
                "slug": row.slug,
                "html_template": row.html_template[:2000],
                "style_id": row.style_id,
                "variables": row.variables,
                "variables_schema": row.variables_schema,
            }
        }

    if action == "create":
        missing = [k for k in ("slug", "document_type", "title", "html_template") if not tool_input.get(k)]
        if missing:
            return {"error": f"create requires {', '.join(missing)}"}
        row = PdfOutputTemplate(
            user_id=user_id,
            slug=tool_input["slug"],
            document_type=tool_input["document_type"],
            title=tool_input["title"],
            html_template=tool_input["html_template"],
            style_id=normalize_prefixed_id("pdf_template_styles", tool_input["style_id"])
            if tool_input.get("style_id")
            else None,
            variables=tool_input.get("variables"),
        )
        db.add(row)
        await db.commit()
        await db.refresh(row)
        return {"item": {"id": row.id, "slug": row.slug}}

    if action == "update":
        if not tool_input.get("template_id"):
            return {"error": "update requires template_id"}
        template_id = normalize_prefixed_id("pdf_output_templates", tool_input["template_id"])
        result = await db.execute(
            select(PdfOutputTemplate).where(PdfOutputTemplate.id == template_id, PdfOutputTemplate.user_id == user_id)
        )
        row = result.scalar_one_or_none()
        if not row:
            return {"error": "not_found"}
        fields = merge_writable_fields(tool_input, _PDF_TEMPLATE_UPDATE_FIELDS)
        if fields.get("style_id"):
            fields["style_id"] = normalize_prefixed_id("pdf_template_styles", fields["style_id"])
        if not fields:
            return {"error": "update requires html_template, style_id, variables, title, slug, document_type, is_default, or is_active"}
        for key, value in fields.items():
            setattr(row, key, value)
        row.version = (row.version or 1) + 1
        await db.commit()
        return {"item": {"id": row.id, "version": row.version, "updated_fields": sorted(fields.keys())}}

    return {"error": f"unknown action: {action}"}


async def _run_pdf_style(db, user_id: str, action: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    """CRUD de pdf_template_styles (CSS)."""
    if action == "list":
        result = await db.execute(
            select(PdfTemplateStyle)
            .where(PdfTemplateStyle.user_id == user_id, PdfTemplateStyle.is_active.is_(True))
            .order_by(PdfTemplateStyle.title)
        )
        rows = result.scalars().all()
        return {
            "items": [
                {"id": r.id, "slug": r.slug, "title": r.title, "description": r.description}
                for r in rows
            ]
        }

    if action == "get":
        q = select(PdfTemplateStyle).where(PdfTemplateStyle.user_id == user_id, PdfTemplateStyle.is_active.is_(True))
        if tool_input.get("style_id"):
            style_id = normalize_prefixed_id("pdf_template_styles", tool_input["style_id"])
            q = q.where(PdfTemplateStyle.id == style_id)
        elif tool_input.get("slug"):
            q = q.where(PdfTemplateStyle.slug == tool_input["slug"])
        else:
            return {"error": "specify style_id or slug"}
        result = await db.execute(q.limit(1))
        row = result.scalar_one_or_none()
        if not row:
            return {"error": "not_found"}
        return {
            "item": {
                "id": row.id,
                "slug": row.slug,
                "title": row.title,
                "description": row.description,
                "css_content": row.css_content,
                "style_guide": row.style_guide,
                "is_active": row.is_active,
            }
        }

    if action == "create":
        missing = [k for k in ("slug", "title", "css_content") if not tool_input.get(k)]
        if missing:
            return {"error": f"create requires {', '.join(missing)}"}
        row = await _PDF_STYLE_REPO.create_for_user(
            db,
            user_id,
            {
                "slug": tool_input["slug"],
                "title": tool_input["title"],
                "css_content": tool_input["css_content"],
                "style_guide": tool_input.get("style_guide"),
                "description": tool_input.get("description"),
            },
        )
        return {"item": {"id": row.id, "slug": row.slug}}

    if action == "update":
        if not tool_input.get("style_id"):
            return {"error": "update requires style_id"}
        style_id = normalize_prefixed_id("pdf_template_styles", tool_input["style_id"])
        fields = merge_writable_fields(tool_input, _PDF_STYLE_UPDATE_FIELDS)
        if not fields:
            return {"error": "update requires style_guide, css_content, title, slug, description, or is_active"}
        row = await _PDF_STYLE_REPO.update_for_user(db, user_id, style_id, fields)
        if not row:
            return {"error": "not_found"}
        payload: Dict[str, Any] = {
            "id": row.id,
            "slug": row.slug,
            "updated_fields": sorted(fields.keys()),
        }
        if "style_guide" in fields:
            payload["style_guide_chars"] = len(row.style_guide or "")
        return {"item": payload}

    return {"error": f"unknown action: {action}"}


async def _load_pdf_template(db, user_id: str, template_id: str) -> Optional[PdfOutputTemplate]:
    template_id = normalize_prefixed_id("pdf_output_templates", template_id)
    result = await db.execute(
        select(PdfOutputTemplate).where(
            PdfOutputTemplate.id == template_id,
            PdfOutputTemplate.user_id == user_id,
            PdfOutputTemplate.is_active.is_(True),
        )
    )
    return result.scalar_one_or_none()


async def _default_pdf_template(db, user_id: str, document_type: str) -> Optional[PdfOutputTemplate]:
    result = await db.execute(
        select(PdfOutputTemplate).where(
            PdfOutputTemplate.user_id == user_id,
            PdfOutputTemplate.document_type == document_type,
            PdfOutputTemplate.is_default.is_(True),
            PdfOutputTemplate.is_active.is_(True),
        )
    )
    row = result.scalar_one_or_none()
    if row:
        return row
    fallback = await db.execute(
        select(PdfOutputTemplate)
        .where(
            PdfOutputTemplate.user_id == user_id,
            PdfOutputTemplate.document_type == document_type,
            PdfOutputTemplate.is_active.is_(True),
        )
        .order_by(PdfOutputTemplate.title)
        .limit(1)
    )
    return fallback.scalar_one_or_none()


def _store_generated_pdf(pdf_bytes: bytes, slug: str, title: str, template_id: str) -> Dict[str, Any]:
    stored = storage_service.upload_file(
        data=io.BytesIO(pdf_bytes),
        original_filename=f"{slug}.pdf",
        size=len(pdf_bytes),
        content_type="application/pdf",
        category="pdf-generated",
        is_public=True,
    )
    url = storage_service.get_public_url(stored)
    return {"pdf_url": url, "filename": stored, "template_id": template_id, "title": title}


async def _render_template_to_pdf(db, row: PdfOutputTemplate, variables: Dict[str, Any], title: str) -> Dict[str, Any]:
    from services.pdf_service import generate_html_template_pdf
    from services.pdf_template_css import resolve_template_css
    from services.pdf_template_render import render_template_html

    html = render_template_html(row.html_template, variables)
    css_content = await resolve_template_css(db, row)
    pdf_bytes = await generate_html_template_pdf(title=title, html_body=html, css_content=css_content)
    return _store_generated_pdf(pdf_bytes, row.slug, title, row.id)


async def _run_generate_pdf(db, user_id: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    row = await _load_pdf_template(db, user_id, tool_input["template_id"])
    if not row:
        return {"error": "not_found"}
    variables = tool_input.get("variables") or {}
    title = tool_input.get("title") or row.title
    return await _render_template_to_pdf(db, row, variables, title)


async def _run_render_record_pdf(db, user_id: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    resource_key = tool_input.get("resource_key") or ""
    meta = PDF_CAPABLE_RESOURCES.get(resource_key)
    if not meta:
        return {
            "error": "resource_not_pdf_capable",
            "allowed": sorted(PDF_CAPABLE_RESOURCES.keys()),
        }
    record_id = tool_input.get("record_id")
    if not record_id:
        return {"error": "record_id required"}
    repo = bedrock_service._get_repository(resource_key)
    record = await repo.get_for_user(db, user_id, record_id)
    if record is None:
        return {"error": "not_found"}
    content = getattr(record, meta["content_attr"], None) or ""
    if not str(content).strip():
        return {"error": "record_has_no_content"}
    title = tool_input.get("title") or getattr(record, meta["title_attr"], None) or resource_key
    if tool_input.get("template_id"):
        row = await _load_pdf_template(db, user_id, tool_input["template_id"])
    else:
        row = await _default_pdf_template(db, user_id, meta["document_type"])
    if not row:
        return {
            "error": "no_template",
            "document_type": meta["document_type"],
            "hint": "Crea una plantilla default con agent_pdf_design o pasa template_id.",
        }
    variables = {"title": title, "content": content, "body": content}
    result = await _render_template_to_pdf(db, row, variables, title)
    result["resource_key"] = resource_key
    result["record_id"] = record.id
    return result


async def _execute_extended(db, user_id: str, name: str, tool_input: Dict[str, Any], session_id: str) -> Dict[str, Any]:
    """Tools nuevos del harness local (no en monolito legacy)."""
    if name == "get_linkedin_status":
        conn = await _linkedin_connection(db, user_id)
        if not conn:
            return {"connected": False}
        return {"connected": True, "member_name": conn.member_name, "expires_at": str(conn.expires_at)}

    if name == "list_linkedin_posts":
        limit = min(tool_input.get("limit", 20), 50)
        result = await db.execute(
            select(LinkedInPost).where(LinkedInPost.user_id == user_id).order_by(desc(LinkedInPost.created_at)).limit(limit)
        )
        posts = result.scalars().all()
        return {
            "items": [
                {"id": p.id, "text": p.text[:200], "status": p.status, "scheduled_at": str(p.scheduled_at) if p.scheduled_at else None}
                for p in posts
            ]
        }

    if name == "create_linkedin_post":
        from services import linkedin_service

        conn = await _linkedin_connection(db, user_id)
        if not conn:
            return {"error": "LinkedIn not connected"}
        text = tool_input["text"]
        scheduled_at = tool_input.get("scheduled_at")
        image_url = tool_input.get("image_url")
        image_bytes = None
        if image_url:
            import httpx

            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.get(image_url)
                r.raise_for_status()
                image_bytes = r.content

        scheduled_dt = None
        if scheduled_at:
            scheduled_dt = datetime.fromisoformat(scheduled_at.replace("Z", "+00:00"))
            if scheduled_dt.tzinfo is None:
                scheduled_dt = scheduled_dt.replace(tzinfo=timezone.utc)

        if scheduled_dt and scheduled_dt > datetime.now(timezone.utc):
            post = LinkedInPost(user_id=user_id, text=text, image_url=image_url, status=LinkedInPostStatus.SCHEDULED, scheduled_at=scheduled_dt)
            db.add(post)
            await db.commit()
            await db.refresh(post)
            return {"scheduled": True, "post_id": post.id, "scheduled_at": str(scheduled_dt)}

        try:
            image_urn = None
            if image_bytes:
                image_urn = await linkedin_service.upload_image(conn.access_token, conn.member_sub, image_bytes)
            post_urn = await linkedin_service.create_post(conn.access_token, conn.member_sub, text, image_urn)
        except Exception as e:
            return {"error": str(e)}
        post = LinkedInPost(
            user_id=user_id, text=text, image_url=image_url, status=LinkedInPostStatus.PUBLISHED,
            linkedin_post_urn=post_urn, published_at=datetime.now(timezone.utc),
        )
        db.add(post)
        await db.commit()
        return {"published": True, "linkedin_post_urn": post_urn}

    if name == "delete_scheduled_linkedin_post":
        post_id = normalize_prefixed_id("linkedin_posts", tool_input["post_id"])
        result = await db.execute(select(LinkedInPost).where(LinkedInPost.id == post_id, LinkedInPost.user_id == user_id))
        post = result.scalar_one_or_none()
        if not post:
            return {"error": "not_found"}
        if post.status != LinkedInPostStatus.SCHEDULED:
            return {"error": "only_scheduled_can_be_deleted"}
        await db.delete(post)
        await db.commit()
        return {"deleted": True}

    if name == "pdf_template" or name in _PDF_TEMPLATE_ALIASES:
        action = tool_input.get("action") or _PDF_TEMPLATE_ALIASES.get(name)
        return await _run_pdf_template(db, user_id, action, tool_input)

    if name == "pdf_style" or name in _PDF_STYLE_ALIASES:
        action = tool_input.get("action") or _PDF_STYLE_ALIASES.get(name)
        return await _run_pdf_style(db, user_id, action, tool_input)

    if name == "list_pdf_capable_resources":
        return {
            "resources": [
                {"resource_key": key, **meta}
                for key, meta in PDF_CAPABLE_RESOURCES.items()
            ]
        }

    if name == "generate_pdf":
        return await _run_generate_pdf(db, user_id, tool_input)

    if name == "render_record_pdf":
        return await _run_render_record_pdf(db, user_id, tool_input)

    if name == "generate_image":
        from services.bedrock.image_client import generate_image_bytes

        w = tool_input.get("width", 1200)
        h = tool_input.get("height", 627)
        data = await generate_image_bytes(tool_input["prompt"], width=w, height=h)
        stored = storage_service.upload_file(
            data=io.BytesIO(data), original_filename="ai-generated.png", size=len(data),
            content_type="image/png", category="ai-generated", is_public=True,
        )
        url = storage_service.get_public_url(stored)
        return {"image_url": url, "filename": stored}

    if name == "attach_image_to_record":
        rk = tool_input["resource_key"]
        if rk not in ("publications", "projects"):
            return {"error": "resource_key must be publications or projects"}
        return await bedrock_service._execute_tool(
            db, user_id, "update_career_record",
            {
                "resource_key": rk,
                "record_id": normalize_prefixed_id(rk, tool_input["record_id"]),
                "fields": {"image_url": tool_input["image_url"]},
            },
            session_id,
        )

    if name == "list_generated_images":
        from models.file_upload import FileUpload

        limit = min(tool_input.get("limit", 20), 50)
        result = await db.execute(
            select(FileUpload).where(FileUpload.user_id == user_id, FileUpload.category == "ai-generated")
            .order_by(desc(FileUpload.created_at)).limit(limit)
        )
        files = result.scalars().all()
        return {"items": [{"filename": f.stored_filename, "url": f.download_url, "description": f.description} for f in files]}

    if name == "delegate_to_specialist":
        return {"error": "delegate_to_specialist must be handled by agent_loop"}

    if name == "list_job_providers":
        from services.job_discovery import providers as list_job_providers

        return {
            "providers": [
                {
                    "id": p.id,
                    "label": p.label,
                    "enabled": p.enabled,
                    "reason": p.reason,
                    "listing_kind": p.listing_kind,
                }
                for p in list_job_providers()
            ]
        }

    if name == "run_job_discovery":
        from services.job_discovery import listing_to_dict, run_discovery

        try:
            result = await run_discovery(
                db,
                user_id,
                query_text=tool_input.get("query"),
                location=tool_input.get("location"),
                providers=tool_input.get("providers"),
                target_role_id=normalize_prefixed_id("target_roles", tool_input["target_role_id"])
                if tool_input.get("target_role_id") is not None
                else None,
                include_company_boards=bool(tool_input.get("include_company_boards")),
                remote=bool(tool_input.get("remote")),
                session_key=session_id,
            )
        except ValueError as exc:
            return {"error": str(exc)}
        return {
            "query": result.query,
            "location": result.location,
            "listings": [listing_to_dict(item) for item in result.listings],
            "errors": [{"provider": e.provider, "message": e.message} for e in result.errors],
            "instruction": (
                "Presenta a Carlos cada listing_kind=job con su ref (L1, L2…). "
                "No llames save_job_listings hasta que autorice refs concretas."
            ),
        }

    if name == "import_job_url":
        from services.job_discovery import import_vacancy_url, listing_to_dict
        from services.job_discovery.preview_store import append_preview

        listing = await import_vacancy_url(tool_input["url"])
        remembered = append_preview(user_id, session_id, listing_to_dict(listing))
        listing.ref = remembered["ref"]
        return listing_to_dict(listing)

    if name == "save_job_listings":
        from services.job_discovery import save_listings
        from services.job_discovery.preview_store import resolve_refs

        refs = tool_input.get("refs") or []
        if not refs:
            return {
                "error": (
                    "Faltan refs autorizadas. Espera a que Carlos elija L1, L3… "
                    "de la última búsqueda. No inventes vacantes."
                )
            }
        found, missing, available = resolve_refs(user_id, session_id, refs)
        if missing:
            return {
                "error": f"Refs no están en la última búsqueda: {missing}.",
                "available_refs": available,
            }
        if not found:
            return {"error": "No hay listings autorizados para guardar.", "available_refs": available}
        return await save_listings(
            db,
            user_id,
            found,
            target_role_id=normalize_prefixed_id("target_roles", tool_input["target_role_id"])
            if tool_input.get("target_role_id") is not None
            else None,
        )

    if name == "web_search":
        from services import web_search_service

        return await web_search_service.search(
            tool_input.get("query") or "",
            max_results=tool_input.get("max_results") or 8,
        )

    if name == "web_fetch":
        from services import web_search_service
        from services.web_search_service import WebSearchError

        try:
            return await web_search_service.fetch(tool_input.get("url") or "")
        except WebSearchError as exc:
            return {"error": str(exc)}

    if name == "get_github_status":
        from services import github_service

        return await github_service.connection_status()

    if name == "list_github_repos":
        from services import github_service

        return await github_service.list_repos(
            db,
            user_id,
            owner=tool_input.get("owner"),
            query=tool_input.get("query"),
            per_page=tool_input.get("per_page") or 30,
        )

    if name in ("get_github_repo", "list_github_contents", "get_github_file", "search_github_code"):
        from services import github_service

        repo = tool_input.get("repo") or ""
        owner = (tool_input.get("owner") or "").strip()
        if not owner and "/" not in repo:
            resolved = await github_service.resolve_owner(db, user_id, None)
            if resolved.get("error"):
                if name != "search_github_code":
                    return resolved
            else:
                owner = resolved["owner"]
        if name == "get_github_repo":
            return await github_service.get_repo(owner, repo)
        if name == "list_github_contents":
            return await github_service.list_contents(
                owner, repo, path=tool_input.get("path") or "", ref=tool_input.get("ref")
            )
        if name == "get_github_file":
            return await github_service.get_file(
                owner, repo, tool_input.get("path") or "", ref=tool_input.get("ref")
            )
        return await github_service.search_code(
            tool_input.get("query") or "", owner=owner or None, repo=repo or None
        )

    raise BedrockError(f"Unknown extended tool: {name}")


# ============================================================================
# Dispatch de tools
# ============================================================================

async def execute_tool(
    db,
    user_id: str,
    name: str,
    tool_input: Dict[str, Any],
    session_id: str,
    caller_profile_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Ejecuta una tool y trunca el resultado."""
    if name in _LEGACY:
        result = await bedrock_service._execute_tool(
            db, user_id, name, tool_input, session_id, caller_profile_id=caller_profile_id
        )
    else:
        result = await _execute_extended(db, user_id, name, tool_input, session_id)
    return truncate_tool_result(result)


def is_write_tool(name: str) -> bool:
    return name in _WRITE_TOOLS


def invalidation_key(name: str, tool_input: Dict[str, Any], tool_result: Dict[str, Any]) -> Optional[str]:
    """Clave para invalidar caché del admin tras un write exitoso (career resource_key o dominio especial)."""
    if tool_result.get("error"):
        return None
    if tool_input.get("resource_key"):
        return str(tool_input["resource_key"])
    if name in ("pdf_template", "create_pdf_template", "update_pdf_template") or name in _PDF_TEMPLATE_ALIASES:
        action = tool_input.get("action") or _PDF_TEMPLATE_ALIASES.get(name)
        if action in ("create", "update") or name in ("create_pdf_template", "update_pdf_template"):
            return "pdf-templates"
    if name in ("pdf_style", "create_pdf_template_style", "update_pdf_template_style") or name in _PDF_STYLE_ALIASES:
        action = tool_input.get("action") or _PDF_STYLE_ALIASES.get(name)
        if action in ("create", "update") or name in ("create_pdf_template_style", "update_pdf_template_style"):
            return "pdf-template-styles"
    if name == "save_job_listings":
        return "vacancies"
    if name in ("generate_pdf", "render_record_pdf"):
        return tool_input.get("resource_key") or "files"
    return None
