"""
Tools Converse — schemas y ejecución (CRUD, LinkedIn, PDF, imágenes).

Tier 1: career CRUD (delegado a bedrock_service._execute_tool).
Tier 2: LinkedIn, plantillas PDF, imágenes, delegación.
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
from repositories.career_repository import CareerRepository
from services import bedrock_service, storage_service
from services.bedrock.errors import BedrockError
from services.bedrock.tool_results import truncate_tool_result

_RESOURCE_KEY_PARAM = {
    "type": "string",
    "description": "resource_key, ej. vacancies, publications, projects",
}

_RECORD_ID_PARAM = {
    "type": "string",
    "description": "ID prefijado del registro, ej. ach-17, cmp-42, vac-7. Usar el id completo.",
}

# Schemas Converse (toolSpec.inputSchema.json)
_RAW_TOOLS: List[Dict[str, Any]] = [
    {"name": "list_recent_changes", "description": "Bitácora reciente del agente.", "schema": {"type": "object", "properties": {"resource_key": {"type": "string"}, "limit": {"type": "integer"}}}},
    {"name": "restore_deleted_record", "description": "Restaura un delete desde audit_id.", "schema": {"type": "object", "properties": {"audit_id": {"type": "integer"}}, "required": ["audit_id"]}},
    {"name": "describe_resource_schema", "description": "Campos válidos de un resource_key.", "schema": {"type": "object", "properties": {"resource_key": _RESOURCE_KEY_PARAM}, "required": ["resource_key"]}},
    {"name": "search_knowledge_base", "description": "Búsqueda semántica Qdrant.", "schema": {"type": "object", "properties": {"query": {"type": "string"}, "top_k": {"type": "integer"}, "type": {"type": "string", "enum": ["methodology", "career_record"]}}, "required": ["query"]}},
    {"name": "list_career_record", "description": "Lista registros paginados.", "schema": {"type": "object", "properties": {"resource_key": _RESOURCE_KEY_PARAM, "search": {"type": "string"}, "limit": {"type": "integer"}, "skip": {"type": "integer"}}, "required": ["resource_key"]}},
    {"name": "get_career_record", "description": "Obtiene un registro por id.", "schema": {"type": "object", "properties": {"resource_key": _RESOURCE_KEY_PARAM, "record_id": _RECORD_ID_PARAM}, "required": ["resource_key", "record_id"]}},
    {"name": "create_career_record", "description": "Crea registro.", "schema": {"type": "object", "properties": {"resource_key": _RESOURCE_KEY_PARAM, "fields": {"type": "object"}}, "required": ["resource_key", "fields"]}},
    {"name": "update_career_record", "description": "Actualiza registro.", "schema": {"type": "object", "properties": {"resource_key": _RESOURCE_KEY_PARAM, "record_id": _RECORD_ID_PARAM, "fields": {"type": "object"}}, "required": ["resource_key", "record_id", "fields"]}},
    {"name": "delete_career_record", "description": "Elimina registro.", "schema": {"type": "object", "properties": {"resource_key": _RESOURCE_KEY_PARAM, "record_id": _RECORD_ID_PARAM}, "required": ["resource_key", "record_id"]}},
    {"name": "get_linkedin_status", "description": "Estado conexión LinkedIn.", "schema": {"type": "object", "properties": {}}},
    {"name": "list_linkedin_posts", "description": "Cola e historial posts LinkedIn.", "schema": {"type": "object", "properties": {"limit": {"type": "integer"}}}},
    {"name": "create_linkedin_post", "description": "Publicar ahora (sin scheduled_at) o programar (ISO futuro).", "schema": {"type": "object", "properties": {"text": {"type": "string"}, "image_url": {"type": "string"}, "scheduled_at": {"type": "string"}}, "required": ["text"]}},
    {"name": "delete_scheduled_linkedin_post", "description": "Elimina post status=scheduled.", "schema": {"type": "object", "properties": {"post_id": {"type": "string", "description": "ID prefijado, ej. lnp-3"}}, "required": ["post_id"]}},
    {"name": "list_pdf_templates", "description": "Lista plantillas PDF del usuario.", "schema": {"type": "object", "properties": {"document_type": {"type": "string"}}}},
    {"name": "get_pdf_template", "description": "Plantilla por id o slug.", "schema": {"type": "object", "properties": {"template_id": {"type": "string", "description": "ID prefijado, ej. pdt-1"}, "slug": {"type": "string"}, "document_type": {"type": "string"}, "default_only": {"type": "boolean"}}}},
    {"name": "create_pdf_template", "description": "Crea plantilla HTML PDF.", "schema": {"type": "object", "properties": {"slug": {"type": "string"}, "document_type": {"type": "string"}, "title": {"type": "string"}, "html_template": {"type": "string"}, "css_content": {"type": "string"}}, "required": ["slug", "document_type", "title", "html_template"]}},
    {"name": "update_pdf_template", "description": "Actualiza plantilla PDF.", "schema": {"type": "object", "properties": {"template_id": {"type": "string", "description": "ID prefijado, ej. pdt-1"}, "fields": {"type": "object"}}, "required": ["template_id", "fields"]}},
    {"name": "generate_pdf", "description": "Genera PDF desde plantilla HTML (template_id) con variables.", "schema": {"type": "object", "properties": {"template_id": {"type": "string", "description": "ID prefijado, ej. pdt-1"}, "variables": {"type": "object"}, "title": {"type": "string"}}, "required": ["template_id"]}},
    {"name": "generate_image", "description": "Genera imagen IA y sube a MinIO.", "schema": {"type": "object", "properties": {"prompt": {"type": "string"}, "purpose": {"type": "string"}, "width": {"type": "integer"}, "height": {"type": "integer"}}, "required": ["prompt"]}},
    {"name": "attach_image_to_record", "description": "Pone image_url en publications o projects.", "schema": {"type": "object", "properties": {"resource_key": {"type": "string"}, "record_id": _RECORD_ID_PARAM, "image_url": {"type": "string"}}, "required": ["resource_key", "record_id", "image_url"]}},
    {"name": "list_generated_images", "description": "Lista imágenes ai-generated.", "schema": {"type": "object", "properties": {"limit": {"type": "integer"}}}},
    {"name": "delegate_to_specialist", "description": "Orquestador: delega a un especialista (solo chat general).", "schema": {"type": "object", "properties": {"agent_profile_id": {"type": "string"}, "task": {"type": "string"}, "context": {"type": "string"}}, "required": ["agent_profile_id", "task"]}},
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
                "target_role_id": {"type": "integer"},
            },
            "required": ["refs"],
        },
    },
]

_WRITE_TOOLS = {"create_career_record", "update_career_record", "delete_career_record", "create_linkedin_post", "create_pdf_template", "update_pdf_template", "generate_pdf", "generate_image", "attach_image_to_record", "save_job_listings"}

_LEGACY = {
    "list_recent_changes", "restore_deleted_record", "describe_resource_schema", "search_knowledge_base",
    "list_career_record", "get_career_record", "create_career_record", "update_career_record", "delete_career_record",
}


def all_tool_names() -> Set[str]:
    return {t["name"] for t in _RAW_TOOLS}


def converse_tool_specs(allowed: Optional[Set[str]] = None) -> List[Dict[str, Any]]:
    """Convierte definiciones a formato toolConfig.tools de Converse API."""
    specs = []
    for t in _RAW_TOOLS:
        if allowed is not None and t["name"] not in allowed:
            continue
        specs.append({
            "toolSpec": {
                "name": t["name"],
                "description": t["description"],
                "inputSchema": {"json": t["schema"]},
            }
        })
    return specs


async def _linkedin_connection(db, user_id: str) -> Optional[LinkedInConnection]:
    result = await db.execute(select(LinkedInConnection).where(LinkedInConnection.user_id == user_id))
    conn = result.scalar_one_or_none()
    if conn and conn.expires_at > datetime.now(timezone.utc):
        return conn
    return None


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
        post_id = tool_input["post_id"]
        result = await db.execute(select(LinkedInPost).where(LinkedInPost.id == post_id, LinkedInPost.user_id == user_id))
        post = result.scalar_one_or_none()
        if not post:
            return {"error": "not_found"}
        if post.status != LinkedInPostStatus.SCHEDULED:
            return {"error": "only_scheduled_can_be_deleted"}
        await db.delete(post)
        await db.commit()
        return {"deleted": True}

    if name == "list_pdf_templates":
        q = select(PdfOutputTemplate).where(PdfOutputTemplate.user_id == user_id, PdfOutputTemplate.is_active.is_(True))
        if tool_input.get("document_type"):
            q = q.where(PdfOutputTemplate.document_type == tool_input["document_type"])
        result = await db.execute(q.order_by(PdfOutputTemplate.title))
        rows = result.scalars().all()
        return {"items": [{"id": r.id, "slug": r.slug, "document_type": r.document_type, "title": r.title, "is_default": r.is_default} for r in rows]}

    if name == "get_pdf_template":
        q = select(PdfOutputTemplate).where(PdfOutputTemplate.user_id == user_id, PdfOutputTemplate.is_active.is_(True))
        if tool_input.get("template_id"):
            q = q.where(PdfOutputTemplate.id == tool_input["template_id"])
        elif tool_input.get("slug"):
            q = q.where(PdfOutputTemplate.slug == tool_input["slug"])
        elif tool_input.get("default_only") and tool_input.get("document_type"):
            q = q.where(PdfOutputTemplate.document_type == tool_input["document_type"], PdfOutputTemplate.is_default.is_(True))
        else:
            return {"error": "specify template_id, slug, or default_only+document_type"}
        result = await db.execute(q.limit(1))
        row = result.scalar_one_or_none()
        if not row:
            return {"error": "not_found"}
        return {"item": {"id": row.id, "slug": row.slug, "html_template": row.html_template[:2000], "variables_schema": row.variables_schema}}

    if name == "create_pdf_template":
        row = PdfOutputTemplate(
            user_id=user_id,
            slug=tool_input["slug"],
            document_type=tool_input["document_type"],
            title=tool_input["title"],
            html_template=tool_input["html_template"],
            css_content=tool_input.get("css_content"),
        )
        db.add(row)
        await db.commit()
        await db.refresh(row)
        return {"item": {"id": row.id, "slug": row.slug}}

    if name == "update_pdf_template":
        result = await db.execute(select(PdfOutputTemplate).where(PdfOutputTemplate.id == tool_input["template_id"], PdfOutputTemplate.user_id == user_id))
        row = result.scalar_one_or_none()
        if not row:
            return {"error": "not_found"}
        for k, v in tool_input.get("fields", {}).items():
            if hasattr(row, k):
                setattr(row, k, v)
        row.version = (row.version or 1) + 1
        await db.commit()
        return {"item": {"id": row.id, "version": row.version}}

    if name == "generate_pdf":
        from services.pdf_service import generate_html_template_pdf
        from services.pdf_template_render import render_template_html

        template_id = tool_input["template_id"]
        result = await db.execute(
            select(PdfOutputTemplate).where(
                PdfOutputTemplate.id == template_id,
                PdfOutputTemplate.user_id == user_id,
                PdfOutputTemplate.is_active.is_(True),
            )
        )
        row = result.scalar_one_or_none()
        if not row:
            return {"error": "not_found"}
        variables = tool_input.get("variables") or {}
        title = tool_input.get("title") or row.title
        html = render_template_html(row.html_template, variables)
        pdf_bytes = await generate_html_template_pdf(title=title, html_body=html, css_content=row.css_content)
        stored = storage_service.upload_file(
            data=io.BytesIO(pdf_bytes),
            original_filename=f"{row.slug}.pdf",
            size=len(pdf_bytes),
            content_type="application/pdf",
            category="pdf-generated",
            is_public=True,
        )
        url = storage_service.get_public_url(stored)
        return {"pdf_url": url, "filename": stored, "template_id": row.id, "title": title}

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
            {"resource_key": rk, "record_id": tool_input["record_id"], "fields": {"image_url": tool_input["image_url"]}},
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
                target_role_id=tool_input.get("target_role_id"),
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
            target_role_id=tool_input.get("target_role_id"),
        )

    raise BedrockError(f"Unknown extended tool: {name}")


async def execute_tool(db, user_id: str, name: str, tool_input: Dict[str, Any], session_id: str) -> Dict[str, Any]:
    """Ejecuta una tool y trunca el resultado."""
    if name in _LEGACY:
        result = await bedrock_service._execute_tool(db, user_id, name, tool_input, session_id)
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
    if name in ("create_pdf_template", "update_pdf_template"):
        return "pdf-templates"
    if name == "save_job_listings":
        return "vacancies"
    return None
