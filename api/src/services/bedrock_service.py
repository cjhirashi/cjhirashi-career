"""
Agent Bedrock — fachada del asistente IA del Admin Panel.

El loop de chat vive en `services/bedrock/` (Harness local Converse API).
Este módulo conserva herramientas CRUD, bitácora, conversaciones PG y
embeddings Titan usados por el harness y por CareerRepository.
"""
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

import boto3

from config import settings
from repositories.career_repository import CareerRepository
from routes.career_common import RESOURCE_REGISTRY
from services import qdrant_service

logger = logging.getLogger(__name__)


class BedrockError(Exception):
    """Raised for any Bedrock/agent failure - callers turn this into an HTTP error."""


# ---------------------------------------------------------------------------
# Configuración de la conexión con AWS - tres clientes boto3 separados, cada
# uno habla con un servicio distinto de Bedrock. Los tres se crean de forma
# perezosa (solo cuando se usan por primera vez) y se guardan como singleton
# a nivel de módulo, para que cada petición reutilice la misma conexión en
# vez de reconectar cada vez:
#   - `bedrock-runtime`           -> _embedding_client: SOLO Titan
#     Embeddings (embed_text). No tiene nada que ver con el agente de chat.
#   - `bedrock-agentcore`         -> _runtime_client: esta es la conexión
#     real con el agente que preguntaste - invoke_harness (el chat) y las
#     llamadas de lectura/escritura de memoria pasan todas por aquí.
#   - `bedrock-agentcore-control` -> _control_client: la API *administrativa*
#     del recurso Harness en sí (leer/cambiar su modelo, consultar su id de
#     memoria) - no se usa para los turnos de chat, solo para configuración.
# Los tres se autentican igual, con el access key/secret plano de IAM que
# viene de `.env` (settings.AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY) - sin
# SSO, sin rol asumido, solo una credencial estática de usuario de servicio.
# ---------------------------------------------------------------------------

_embedding_client = None
_repositories: Dict[str, CareerRepository] = {}


def _require_configured() -> None:
    if not settings.AWS_ACCESS_KEY_ID or not settings.AWS_SECRET_ACCESS_KEY:
        raise BedrockError("Bedrock is not configured (missing AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY)")


def _get_embedding_client():
    """`bedrock-runtime` client, used only for Titan Embeddings - the
    knowledge base embeds text directly, outside of the harness."""
    global _embedding_client
    _require_configured()
    if _embedding_client is None:
        _embedding_client = boto3.client(
            "bedrock-runtime",
            region_name=settings.BEDROCK_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
    return _embedding_client


def _get_repository(resource_key: str) -> CareerRepository:
    """Una instancia de `CareerRepository` por recurso, reutilizada entre
    llamadas (es barato de construir, pero no hay razón para reconstruirlo
    en cada llamada a herramienta). Es exactamente la misma clase de
    repositorio que ya usa cada ruta CRUD genérica `/career/{key}` - las
    herramientas del agente de más abajo no reimplementan el acceso a
    datos, solo llaman a esto."""
    if resource_key not in RESOURCE_REGISTRY:
        raise BedrockError(f"Unknown resource_key: {resource_key}")
    if resource_key not in _repositories:
        _repositories[resource_key] = CareerRepository(RESOURCE_REGISTRY[resource_key], resource_key=resource_key)
    return _repositories[resource_key]


async def embed_text(text: str) -> List[float]:
    """Embed `text` with Bedrock Titan Embeddings. Runs boto3's sync call in
    a thread since boto3 has no native async support."""
    client = _get_embedding_client()

    def _invoke():
        response = client.invoke_model(
            modelId=settings.BEDROCK_EMBEDDING_MODEL_ID,
            body=json.dumps({"inputText": text}),
        )
        return json.loads(response["body"].read())

    try:
        result = await asyncio.to_thread(_invoke)
    except Exception as e:
        raise BedrockError(f"Embedding request failed: {e}") from e
    return result["embedding"]


# ---------------------------------------------------------------------------
# Cambio de modelo
# ---------------------------------------------------------------------------

async def get_current_model() -> str:
    """Modelo activo — Harness local lee PG; legacy lee AgentCore harness."""
    from services.bedrock.agent_loop import use_local_harness
    from services.bedrock.settings_loader import get_active_model_id
    from database import AsyncSessionLocal

    if use_local_harness():
        async with AsyncSessionLocal() as db:
            return await get_active_model_id(db)

    raise BedrockError("Harness local desactivado. Configure BEDROCK_USE_LOCAL_HARNESS=true y credenciales AWS.")


async def switch_model(model_id: str) -> None:
    """Cambia modelo activo — PG (local) o UpdateHarness (legacy)."""
    if model_id not in settings.BEDROCK_AVAILABLE_MODELS:
        raise BedrockError(f"Model not in the allow-list: {model_id}")

    from services.bedrock.agent_loop import use_local_harness
    from services.bedrock.settings_loader import set_active_model_id
    from database import AsyncSessionLocal

    if use_local_harness():
        async with AsyncSessionLocal() as db:
            await set_active_model_id(db, model_id)
        return

    raise BedrockError("Harness local desactivado. Configure BEDROCK_USE_LOCAL_HARNESS=true y credenciales AWS.")


# ---------------------------------------------------------------------------
# Herramientas expuestas al harness (herramientas inline_function). Esta es
# la lista que se le manda a AWS en cada invoke_harness (ver `tools` en
# chat_stream) - el modelo decide solo, en base al nombre/descripción de
# cada una, cuál usar y con qué argumentos (definidos en su inputSchema,
# formato JSON Schema estándar). La ejecución real de cada una vive en
# `_execute_tool`, más abajo.
# ---------------------------------------------------------------------------

_RESOURCE_KEY_PARAM = {
    "type": "string",
    "description": "The resource key, e.g. 'vacancies', 'projects', 'operational-methodologies'.",
}

_RECORD_ID_PARAM = {
    "type": "string",
    "description": "Prefixed record id, e.g. ach-17, cmp-42, vac-7. Use the full id as shown in lists.",
}

_BUILTIN_TOOLS = [
    {
        "type": "inline_function",
        "name": "list_recent_changes",
        "config": {
            "inlineFunction": {
                "description": (
                    "List recent entries from the audit log (bitácora) of changes you've made - every "
                    "create/update/delete you've done, with the full record state before and after. Use "
                    "this to answer 'what did you just do', to double-check a change before Carlos asks, "
                    "or to find the audit_id of a delete you need to undo with restore_deleted_record."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "resource_key": {
                            "type": "string",
                            "description": "Optional filter to only one resource's changes.",
                        },
                        "limit": {"type": "integer", "description": "Max entries, default 10."},
                    },
                },
            }
        },
    },
    {
        "type": "inline_function",
        "name": "restore_deleted_record",
        "config": {
            "inlineFunction": {
                "description": (
                    "Undo a delete you made - re-creates the record from an audit log entry's saved state "
                    "(the row exactly as it was right before you deleted it). Get the audit_id from "
                    "list_recent_changes first. Only works on 'delete' entries."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {"audit_id": {"type": "integer"}},
                    "required": ["audit_id"],
                },
            }
        },
    },
    {
        "type": "inline_function",
        "name": "describe_resource_schema",
        "config": {
            "inlineFunction": {
                "description": (
                    "Get the exact field names accepted by create_career_record/update_career_record "
                    "for one resource. Call this before creating a record on a resource whose fields "
                    "you're not already sure of (field names don't always match what you'd guess, e.g. "
                    "the 'tags' resource uses 'tag_name'/'entity_type', not 'name'/'category') - cheaper "
                    "than a failed create_career_record call and a knowledge-base detour to recover."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {"resource_key": _RESOURCE_KEY_PARAM},
                    "required": ["resource_key"],
                },
            }
        },
    },
    {
        "type": "inline_function",
        "name": "search_knowledge_base",
        "config": {
            "inlineFunction": {
                "description": (
                    "Semantic search over the local knowledge base: operational methodologies "
                    "(how to work each table) and real career records. Use this whenever you need "
                    "guidance on how to operate a domain, or to find records by meaning rather than "
                    "an exact id."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Natural-language search query."},
                        "top_k": {"type": "integer", "description": "Max results, default 5."},
                        "type": {
                            "type": "string",
                            "enum": ["methodology", "career_record"],
                            "description": "Optional filter to only one kind of content.",
                        },
                    },
                    "required": ["query"],
                },
            }
        },
    },
    {
        "type": "inline_function",
        "name": "list_career_record",
        "config": {
            "inlineFunction": {
                "description": "List/search records of one resource, paginated.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "resource_key": _RESOURCE_KEY_PARAM,
                        "search": {"type": "string", "description": "Optional free-text filter."},
                        "sort_by": {"type": "string", "description": "Optional column name to sort by."},
                        "sort_dir": {"type": "string", "enum": ["asc", "desc"]},
                        "limit": {"type": "integer", "description": "Default 20, max 100."},
                        "skip": {"type": "integer", "description": "Pagination offset, default 0."},
                    },
                    "required": ["resource_key"],
                },
            }
        },
    },
    {
        "type": "inline_function",
        "name": "get_career_record",
        "config": {
            "inlineFunction": {
                "description": "Fetch one full record by id.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"resource_key": _RESOURCE_KEY_PARAM, "record_id": _RECORD_ID_PARAM},
                    "required": ["resource_key", "record_id"],
                },
            }
        },
    },
    {
        "type": "inline_function",
        "name": "create_career_record",
        "config": {
            "inlineFunction": {
                "description": "Create a new record. `fields` is an object of column name -> value.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "resource_key": _RESOURCE_KEY_PARAM,
                        "fields": {"type": "object", "description": "Column name -> value."},
                    },
                    "required": ["resource_key", "fields"],
                },
            }
        },
    },
    {
        "type": "inline_function",
        "name": "update_career_record",
        "config": {
            "inlineFunction": {
                "description": "Update an existing record. `fields` only needs the columns that change.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "resource_key": _RESOURCE_KEY_PARAM,
                        "record_id": _RECORD_ID_PARAM,
                        "fields": {"type": "object", "description": "Column name -> new value."},
                    },
                    "required": ["resource_key", "record_id", "fields"],
                },
            }
        },
    },
    {
        "type": "inline_function",
        "name": "delete_career_record",
        "config": {
            "inlineFunction": {
                "description": "Permanently delete a record.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"resource_key": _RESOURCE_KEY_PARAM, "record_id": _RECORD_ID_PARAM},
                    "required": ["resource_key", "record_id"],
                },
            }
        },
    },
]

_WRITE_TOOLS = {"create_career_record", "update_career_record", "delete_career_record"}


async def _active_tools(db) -> List[Dict[str, Any]]:
    """Las herramientas propias más cada `BedrockCustomTool` habilitada
    (servidores MCP que Carlos registró desde la app - ver los endpoints
    /tools de routes/bedrock.py), como entradas de tipo `remote_mcp`. Así
    es como se agregan capacidades nuevas sin un deploy de código: se
    registra la URL de un servidor MCP y sus herramientas quedan
    disponibles en el siguiente turno."""
    from sqlalchemy import select

    from models.bedrock_custom_tool import BedrockCustomTool

    result = await db.execute(select(BedrockCustomTool).where(BedrockCustomTool.is_enabled.is_(True)))
    custom_tools = [
        {
            "type": "remote_mcp",
            "name": tool.name,
            "config": {"remoteMcp": {"url": tool.url, **({"headers": tool.headers} if tool.headers else {})}},
        }
        for tool in result.scalars().all()
    ]
    return _BUILTIN_TOOLS + custom_tools


async def list_custom_tools(db) -> List["BedrockCustomTool"]:  # noqa: F821 - imported below for the type only
    from sqlalchemy import select

    from models.bedrock_custom_tool import BedrockCustomTool

    result = await db.execute(select(BedrockCustomTool).order_by(BedrockCustomTool.created_at.desc()))
    return result.scalars().all()


async def create_custom_tool(db, name: str, url: str, headers: Optional[Dict[str, str]] = None) -> "BedrockCustomTool":  # noqa: F821
    from models.bedrock_custom_tool import BedrockCustomTool

    tool = BedrockCustomTool(name=name, url=url, headers=headers or None, is_enabled=True)
    db.add(tool)
    await db.flush()
    await db.refresh(tool)
    await db.commit()
    return tool


async def set_custom_tool_enabled(db, tool_id: str, is_enabled: bool) -> Optional["BedrockCustomTool"]:  # noqa: F821
    from sqlalchemy import select

    from models.bedrock_custom_tool import BedrockCustomTool

    result = await db.execute(select(BedrockCustomTool).where(BedrockCustomTool.id == tool_id))
    tool = result.scalar_one_or_none()
    if tool is None:
        return None
    tool.is_enabled = is_enabled
    await db.commit()
    await db.refresh(tool)
    return tool


async def delete_custom_tool(db, tool_id: str) -> bool:
    from sqlalchemy import select

    from models.bedrock_custom_tool import BedrockCustomTool

    result = await db.execute(select(BedrockCustomTool).where(BedrockCustomTool.id == tool_id))
    tool = result.scalar_one_or_none()
    if tool is None:
        return False
    await db.delete(tool)
    await db.commit()
    return True


# ---------------------------------------------------------------------------
# Motor de ejecución de herramientas - `_execute_tool` es el despachador que
# `chat_stream` llama cada vez que el harness se pausa con
# `stop_reason == "tool_use"` (cada herramienta `inline_function` definida
# arriba corresponde a un `if` aquí, según su nombre). Todo esto corre
# LOCALMENTE, en este proceso - el harness nunca toca la base de datos ni
# Qdrant directamente, solo decide *qué* herramienta llamar y *con qué
# argumentos*; esta función es la que realmente hace el trabajo y devuelve
# el resultado.
# ---------------------------------------------------------------------------


def _serialize(obj: Any) -> Dict[str, Any]:
    """SQLAlchemy row -> plain dict of its real columns, JSON-safe (dates,
    Decimals, enums, etc. get stringified before going back to the model)."""
    from sqlalchemy import inspect as sa_inspect

    if obj is None:
        return {}
    result: Dict[str, Any] = {}
    for attr in sa_inspect(obj).mapper.column_attrs:
        value = getattr(obj, attr.key)
        result[attr.key] = value if isinstance(value, (dict, list, int, float, bool, str)) or value is None else str(value)
    return result


def _normalize_record_id(resource_key: str, record_id: Any) -> str:
    """Convierte record_id al formato prefijado (ej. 17 → ach-17 si resource_key=achievements)."""
    from services.id_generator import TABLE_PREFIXES

    if isinstance(record_id, str):
        stripped = record_id.strip()
        if "-" in stripped:
            return stripped
        if stripped.isdigit():
            prefix = TABLE_PREFIXES.get(resource_key)
            if prefix:
                return f"{prefix}-{stripped}"
        return stripped
    if isinstance(record_id, int):
        prefix = TABLE_PREFIXES.get(resource_key)
        if prefix:
            return f"{prefix}-{record_id}"
    return str(record_id)


async def _record_audit(
    db,
    *,
    user_id: str,
    action: str,
    resource_key: str,
    record_id: Optional[str],
    old_values: Optional[Dict[str, Any]],
    new_values: Optional[Dict[str, Any]],
    session_id: str,
) -> None:
    """Every write the agent makes, logged with the full before/after record
    state - specifically so a mistaken delete is recoverable (old_values has
    the complete row, not just its id). Not best-effort like the Qdrant
    indexing hook: an audit trail that can silently fail to record a delete
    defeats its own purpose, so a failure here raises and the caller
    (chat_stream) surfaces it as a tool error rather than pretending the
    write was clean."""
    from models.audit_log import AuditAction, AuditLog

    db.add(
        AuditLog(
            user_id=user_id,
            action=AuditAction(action),
            resource_type=resource_key,
            resource_id=record_id,
            old_values=old_values,
            new_values=new_values,
            reason="Agent Bedrock",
            extra_metadata={"session_id": session_id},
        )
    )
    await db.commit()


async def _execute_tool(db, user_id: str, name: str, tool_input: Dict[str, Any], session_id: str) -> Dict[str, Any]:
    """Run one tool call, scoped to `user_id` throughout - same isolation
    guarantee as every other authenticated route in this API."""
    if name == "search_knowledge_base":
        vector = await embed_text(tool_input["query"])
        results = await qdrant_service.search(
            user_id=user_id,
            vector=vector,
            top_k=tool_input.get("top_k", 5),
            resource_type=tool_input.get("type"),
        )
        return {"results": results}

    if name == "list_career_record":
        repo = _get_repository(tool_input["resource_key"])
        items = await repo.list_for_user(
            db,
            user_id,
            skip=tool_input.get("skip", 0),
            limit=min(tool_input.get("limit", 20), 100),
            sort_by=tool_input.get("sort_by"),
            sort_dir=tool_input.get("sort_dir", "asc"),
            search=tool_input.get("search"),
        )
        return {"items": [_serialize(item) for item in items]}

    if name == "get_career_record":
        repo = _get_repository(tool_input["resource_key"])
        record_id = _normalize_record_id(tool_input["resource_key"], tool_input["record_id"])
        item = await repo.get_for_user(db, user_id, record_id)
        if item is None:
            return {"error": "not_found"}
        return {"item": _serialize(item)}

    if name == "describe_resource_schema":
        repo = _get_repository(tool_input["resource_key"])
        return {"fields": sorted(repo._indexable_columns)}

    if name == "list_recent_changes":
        entries = await list_audit_log(db, user_id, limit=min(tool_input.get("limit", 10), 50))
        resource_filter = tool_input.get("resource_key")
        if resource_filter:
            entries = [e for e in entries if e.resource_type == resource_filter]
        return {
            "entries": [
                {
                    "audit_id": e.id,
                    "action": e.action.value,
                    "resource_key": e.resource_type,
                    "record_id": e.resource_id,
                    "created_at": str(e.created_at),
                }
                for e in entries
            ]
        }

    if name == "restore_deleted_record":
        try:
            restored = await restore_audit_entry(db, user_id, tool_input["audit_id"])
        except BedrockError as e:
            return {"error": str(e)}
        return {"item": restored}

    if name == "create_career_record":
        resource_key = tool_input["resource_key"]
        repo = _get_repository(resource_key)
        invalid = _invalid_fields_error(repo, tool_input["fields"])
        if invalid:
            return invalid
        item = await repo.create_for_user(db, user_id, tool_input["fields"])
        serialized = _serialize(item)
        await _record_audit(
            db,
            user_id=user_id,
            action="create",
            resource_key=resource_key,
            record_id=item.id,
            old_values=None,
            new_values=serialized,
            session_id=session_id,
        )
        return {"item": serialized}

    if name == "update_career_record":
        resource_key = tool_input["resource_key"]
        repo = _get_repository(resource_key)
        invalid = _invalid_fields_error(repo, tool_input["fields"])
        if invalid:
            return invalid
        record_id = _normalize_record_id(resource_key, tool_input["record_id"])
        before = await repo.get_for_user(db, user_id, record_id)
        if before is None:
            return {"error": "not_found"}
        before_serialized = _serialize(before)
        item = await repo.update_for_user(db, user_id, record_id, tool_input["fields"])
        serialized = _serialize(item)
        await _record_audit(
            db,
            user_id=user_id,
            action="update",
            resource_key=resource_key,
            record_id=item.id,
            old_values=before_serialized,
            new_values=serialized,
            session_id=session_id,
        )
        return {"item": serialized}

    if name == "delete_career_record":
        resource_key = tool_input["resource_key"]
        repo = _get_repository(resource_key)
        record_id = _normalize_record_id(resource_key, tool_input["record_id"])
        # Captured BEFORE the delete - this is the row the audit log exists
        # to preserve. Without it, a mistaken delete is unrecoverable (this
        # feature exists precisely because that already happened once).
        before = await repo.get_for_user(db, user_id, record_id)
        if before is None:
            return {"deleted": False}
        before_serialized = _serialize(before)
        deleted = await repo.delete_for_user(db, user_id, record_id)
        if deleted:
            await _record_audit(
                db,
                user_id=user_id,
                action="delete",
                resource_key=resource_key,
                record_id=record_id,
                old_values=before_serialized,
                new_values=None,
                session_id=session_id,
            )
        return {"deleted": deleted}

    raise BedrockError(f"Unknown tool: {name}")


# ---------------------------------------------------------------------------
# Bitácora (audit log) - lectura + restauración. La escritura pasa en
# _execute_tool/_record_audit más arriba; esto es el lado de Carlos (la
# página Bitácora).
# ---------------------------------------------------------------------------

async def list_audit_log(db, user_id: str, limit: int = 50, offset: int = 0) -> List["AuditLog"]:  # noqa: F821
    from sqlalchemy import select

    from models.audit_log import AuditLog

    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.user_id == user_id, AuditLog.reason == "Agent Bedrock")
        .order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return result.scalars().all()


async def restore_audit_entry(db, user_id: str, audit_id: str) -> Dict[str, Any]:
    """Deshace un delete que hizo el agente: recrea el registro a partir de
    `old_values` de la entrada de bitácora (la fila completa capturada
    justo antes del delete). Solo tiene sentido para entradas `delete` - un
    create/update no tiene a qué "restaurarse" que no sea ya la fila
    actual."""
    from sqlalchemy import select

    from models.audit_log import AuditLog

    result = await db.execute(select(AuditLog).where(AuditLog.id == audit_id, AuditLog.user_id == user_id))
    entry = result.scalar_one_or_none()
    if entry is None:
        raise BedrockError("Audit log entry not found")
    if entry.action.value != "delete" or not entry.old_values:
        raise BedrockError("Only a 'delete' entry with saved old_values can be restored")

    repo = _get_repository(entry.resource_type)
    # Drop columns the DB assigns itself - re-inserting the exact old id
    # isn't guaranteed possible (a new row may already have reused it) and
    # timestamps should reflect the restore, not the original creation.
    fields = {k: v for k, v in entry.old_values.items() if k not in ("id", "user_id", "created_at", "updated_at")}
    item = await repo.create_for_user(db, user_id, fields)
    serialized = _serialize(item)
    await _record_audit(
        db,
        user_id=user_id,
        action="create",
        resource_key=entry.resource_type,
        record_id=item.id,
        old_values=None,
        new_values=serialized,
        session_id="restore-from-audit-log",
    )
    return serialized


def _invalid_fields_error(repo: CareerRepository, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Reject unknown column names before they ever reach SQLAlchemy, with
    the real column list in the error - without this, a wrong guess (e.g.
    `name` instead of `tag_name`) surfaces as a generic ORM TypeError that
    tells the model nothing about what the right field is, burning an extra
    search_knowledge_base + retry round-trip (measured: 4-6 tool calls for
    what should take 1-2) just to rediscover the schema by trial and error."""
    valid = set(repo._indexable_columns)
    unknown = sorted(set(fields.keys()) - valid)
    if not unknown:
        return None
    return {
        "error": f"Unknown field(s) {unknown} for this resource.",
        "valid_fields": sorted(valid),
    }


# ---------------------------------------------------------------------------
# System prompt - quién es el agente y cómo debe comportarse. Se envía de
# nuevo en cada llamada a `invoke_harness` (ver chat_stream), no se
# configura una sola vez en el recurso Harness - eso es lo que permite que
# Carlos lo edite desde la app (/bedrock/instructions) y que aplique en el
# siguiente mensaje, sin llamada al plano de control de AWS ni redeploy.
# ---------------------------------------------------------------------------


def default_system_prompt() -> str:
    resource_list = ", ".join(sorted(RESOURCE_REGISTRY.keys()))
    return (
        "Eres el asistente de carrera dentro del Admin Panel de Carlos Jiménez Hirashi. "
        "Tienes acceso completo de lectura y escritura sobre sus datos de carrera a través de tus "
        "herramientas - puedes listar, obtener, crear, actualizar y eliminar registros directamente, "
        "sin pedir confirmación adicional del sistema (Carlos ya te la dio al usarte). "
        "Antes de operar una tabla que no conozcas bien, usa search_knowledge_base para consultar la "
        "metodología operativa correspondiente - ahí está documentado cómo se relacionan las tablas "
        "entre sí y qué disciplina seguir en cada una. Esas metodologías (resource_key "
        "'operational-methodologies') también son tuyas para mantener: si Carlos te pide documentar o "
        "corregir cómo se opera una tabla, o si notas que una metodología quedó desactualizada tras un "
        "cambio, créala o actualízala tú mismo con las mismas herramientas de escritura. "
        "Antes de crear un registro en un recurso cuyos campos exactos no tengas ya confirmados (por un "
        "list_career_record o get_career_record previo en esta misma conversación), llama primero a "
        "describe_resource_schema - los nombres de columna reales no siempre son los que se adivinarían "
        "(ej. 'tags' usa tag_name/entity_type, no name/category). Evita adivinar campos a ciegas. "
        "Para una petición de varios pasos (ej. 'actualiza toda mi sección de Identidad' o cualquier tarea "
        "que tome más de 2-3 llamadas a herramientas), usa el resource_key 'agent-tasks' (fields: title, "
        "description, status) para planear primero: crea una tarea por paso con status='pending', y ve "
        "actualizando cada una a 'in_progress' antes de ejecutarla y a 'done' al terminarla (o "
        "'cancelled' si ya no aplica) - así Carlos puede ver el plan avanzar, y tú puedes retomarlo en "
        "otra conversación si esta se corta a la mitad. Para un mensaje simple de un solo paso, no hace "
        "falta crear una tarea. "
        "Cada create/update/delete que haces queda registrado automáticamente en la bitácora, con el "
        "estado completo del registro antes y después - no necesitas escribir nada ahí tú mismo. Usa "
        "list_recent_changes si Carlos pregunta qué hiciste, o si necesitas confirmar un cambio antes de "
        "seguir. Si Carlos te pide deshacer algo que eliminaste (en esta conversación o una anterior), "
        "usa list_recent_changes para encontrar el audit_id de esa eliminación y luego "
        "restore_deleted_record - no lo recrees a mano con create_career_record, el registro restaurado "
        "debe salir exactamente del estado que guardó la bitácora. "
        "Responde siempre en español, de forma clara y directa sobre qué hiciste. "
        "No envuelvas la respuesta al usuario en etiquetas de razonamiento interno "
        "(<thinking>, </thinking>, <think>, </think>). "
        f"Recursos disponibles (resource_key): {resource_list}."
    )


async def get_system_prompt(db) -> str:
    """The active system prompt - Carlos's override if he's set one (see
    /bedrock/instructions), otherwise the built-in default. Read fresh on
    every turn (see chat_stream) rather than cached, so an edit takes effect
    on the very next message."""
    from sqlalchemy import select

    from models.bedrock_settings import BedrockSettings

    result = await db.execute(select(BedrockSettings).limit(1))
    row = result.scalar_one_or_none()
    if row and row.system_prompt:
        return row.system_prompt
    return default_system_prompt()


async def set_system_prompt(db, text: Optional[str]) -> str:
    """Set (or, with `text=None`, clear) the override. Returns the resulting
    active prompt. Single-row table (`BedrockSettings` is a single-operator
    setting, not per-user) - creates the row on first use."""
    from sqlalchemy import select

    from models.bedrock_settings import BedrockSettings

    result = await db.execute(select(BedrockSettings).limit(1))
    row = result.scalar_one_or_none()
    if row is None:
        row = BedrockSettings(system_prompt=text)
        db.add(row)
    else:
        row.system_prompt = text
    await db.commit()
    return await get_system_prompt(db)


# ---------------------------------------------------------------------------
# Conversaciones - historial guardado del lado del servidor, para que sea
# el mismo en cualquier dispositivo en vez de vivir en el localStorage de
# un solo navegador. El `session_id` de aquí es exactamente el mismo id que
# se le pasa a invoke_harness como runtimeSessionId (ver chat_stream) - una
# fila por conversación, no un segundo id que mantener sincronizado.
# ---------------------------------------------------------------------------

def _conversation_title_from(text: str) -> str:
    return text[:60] + "…" if len(text) > 60 else text


async def _get_or_create_conversation(db, user_id: str, session_id: str, first_message: str) -> "BedrockConversation":  # noqa: F821
    from sqlalchemy import select

    from models.bedrock_conversation import BedrockConversation

    result = await db.execute(
        select(BedrockConversation).where(
            BedrockConversation.session_id == session_id, BedrockConversation.user_id == user_id
        )
    )
    conversation = result.scalar_one_or_none()
    if conversation is None:
        conversation = BedrockConversation(
            user_id=user_id, session_id=session_id, title=_conversation_title_from(first_message)
        )
        db.add(conversation)
        await db.flush()
    return conversation


async def _append_message(db, conversation: "BedrockConversation", role: str, content: str) -> None:  # noqa: F821
    from datetime import datetime, timezone

    from models.bedrock_conversation import BedrockConversationMessage

    db.add(BedrockConversationMessage(conversation_id=conversation.id, role=role, content=content))
    # Adding a child message doesn't dirty the parent row on its own -
    # `onupdate=func.now()` only fires when one of the parent's own columns
    # actually changes, so this bump is what keeps `list_conversations`'s
    # "most recently active" ordering correct.
    conversation.updated_at = datetime.now(timezone.utc)
    await db.commit()


async def list_conversations(db, user_id: str) -> List["BedrockConversation"]:  # noqa: F821
    from sqlalchemy import select

    from models.bedrock_conversation import BedrockConversation

    result = await db.execute(
        select(BedrockConversation)
        .where(BedrockConversation.user_id == user_id)
        .order_by(BedrockConversation.updated_at.desc())
    )
    return result.scalars().all()


async def get_conversation_messages(db, user_id: str, session_id: str) -> List["BedrockConversationMessage"]:  # noqa: F821
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from models.bedrock_conversation import BedrockConversation

    result = await db.execute(
        select(BedrockConversation)
        .options(selectinload(BedrockConversation.messages))
        .where(BedrockConversation.session_id == session_id, BedrockConversation.user_id == user_id)
    )
    conversation = result.scalar_one_or_none()
    return conversation.messages if conversation else []


async def rename_conversation(db, user_id: str, session_id: str, title: str) -> bool:
    from sqlalchemy import select

    from models.bedrock_conversation import BedrockConversation

    result = await db.execute(
        select(BedrockConversation).where(
            BedrockConversation.session_id == session_id, BedrockConversation.user_id == user_id
        )
    )
    conversation = result.scalar_one_or_none()
    if conversation is None:
        return False
    conversation.title = title[:255]
    await db.commit()
    return True


async def delete_conversation(db, user_id: str, session_id: str) -> bool:
    from sqlalchemy import select

    from models.bedrock_conversation import BedrockConversation

    result = await db.execute(
        select(BedrockConversation).where(
            BedrockConversation.session_id == session_id, BedrockConversation.user_id == user_id
        )
    )
    conversation = result.scalar_one_or_none()
    if conversation is None:
        return False
    await db.delete(conversation)
    await db.commit()
    return True


# ---------------------------------------------------------------------------
# EL LOOP DEL AGENTE - esta es la conexión real con el agente que Carlos
# preguntó. `chat_stream` es la única función que le habla a
# `invoke_harness`; todo lo de arriba (herramientas, system prompt,
# memoria, repositorios) existe para ser usado DESDE aquí. `chat` es solo
# un envoltorio delgado para quien no necesita ver el progreso paso a paso.
# ---------------------------------------------------------------------------


async def chat(db, user_id: str, session_id: str, message: str) -> Dict[str, Any]:
    """Run one chat turn against the harness. The harness owns the
    conversation history server-side (keyed by `session_id`) - callers only
    ever send the newest user message, never the full history.

    Returns `{"reply": str, "affected_resources": list[str]}` -
    `affected_resources` lists every resource_key touched by a write tool
    this turn, so the frontend can invalidate its cache for those tables.

    Thin wrapper around `chat_stream` for callers that don't care about
    intermediate progress - drains the generator and returns its final event.
    """
    async for event in chat_stream(db, user_id, session_id, message):
        if event["type"] == "done":
            return {"reply": event["reply"], "affected_resources": event["affected_resources"]}
    raise BedrockError("chat_stream ended without a final answer")


_TOOL_STATUS_MESSAGES = {
    "describe_resource_schema": "Revisando la estructura de la tabla...",
    "search_knowledge_base": "Consultando la base de conocimiento...",
    "list_career_record": "Buscando registros...",
    "get_career_record": "Consultando el registro...",
    "create_career_record": "Creando el registro...",
    "update_career_record": "Actualizando el registro...",
    "delete_career_record": "Eliminando el registro...",
    "list_recent_changes": "Consultando la bitácora...",
    "restore_deleted_record": "Restaurando el registro...",
}


async def chat_stream(db, user_id: str, session_id: str, message: str, turn_request=None):
    """Loop agente — Harness local (Converse) o legacy AgentCore."""
    from services.bedrock.agent_loop import chat_stream as local_chat_stream, use_local_harness
    from services.bedrock.agent_loop import ChatTurnRequest

    if use_local_harness():
        req = turn_request or ChatTurnRequest(session_id=session_id, message=message)
        async for event in local_chat_stream(db, user_id, req):
            yield event
        return

    raise BedrockError(
        "AgentCore Harness eliminado. Use BEDROCK_USE_LOCAL_HARNESS=true (ver docs/BEDROCK-SYSTEM.md)."
    )
