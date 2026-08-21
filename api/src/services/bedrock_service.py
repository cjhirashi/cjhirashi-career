"""
Agent Bedrock - el asistente de IA del Admin Panel, corriendo dentro del
mismo proceso del API REST.

Según la arquitectura del proyecto (docs/04-SOLUTION-STRATEGY.md Decisión
5, docs/06-RUNTIME-VIEW.md Escenario 4): Bedrock no tiene contenedor
propio, ni puerto, ni autenticación propia - se invoca en el mismo proceso
del API REST, heredando el JWT de la sesión del Admin Panel que lo llamó.
Este módulo ES esa invocación, construida sobre Amazon Bedrock AgentCore
Harness (no un loop de Converse hecho a mano): `invoke_harness` se encarga
de la llamada al modelo, de la señalización de orquestación de uso de
herramientas y de la memoria de sesión del lado de AWS (indexada por
`runtimeSessionId`) - este módulo solo necesita ejecutar las herramientas
`inline_function` cuando el harness se pausa a pedir una, y devolverle el
resultado. Las herramientas en sí operan directo sobre `CareerRepository`
(la misma clase exacta que ya usa cada ruta CRUD genérica) y sobre la base
de conocimiento en Qdrant (`qdrant_service.py`).

Las capacidades del agente - lectura/escritura/creación/eliminación
completa sobre cualquiera de los ~30 recursos del dominio de carrera, y
búsqueda semántica sobre su base de conocimiento - son una decisión de
producto deliberada (no algo que este módulo restrinja): cada escritura
pasa directo por `CareerRepository`, sin un paso intermedio de
"propuesta".

Cambio de modelo: el modelo no es un parámetro por invocación, es parte de
la configuración propia del recurso Harness. `switch_model` llama al plano
de control `UpdateHarness`, que crea una nueva versión inmutable del
harness y mueve el endpoint DEFAULT del harness a esa versión -
`get_current_model` siempre refleja el valor real leyendo el harness de
nuevo, en vez de guardarlo en caché localmente, ya que el harness mismo es
la única fuente de verdad aquí.
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
_runtime_client = None
_control_client = None
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


def _get_runtime_client():
    """`bedrock-agentcore` data-plane client - `invoke_harness`."""
    global _runtime_client
    _require_configured()
    if _runtime_client is None:
        _runtime_client = boto3.client(
            "bedrock-agentcore",
            region_name=settings.BEDROCK_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
    return _runtime_client


def _get_control_client():
    """`bedrock-agentcore-control` control-plane client - `get_harness`/`update_harness`."""
    global _control_client
    _require_configured()
    if _control_client is None:
        _control_client = boto3.client(
            "bedrock-agentcore-control",
            region_name=settings.BEDROCK_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
    return _control_client


def _harness_id() -> str:
    """The harness ARN's last path segment is its id - `get_harness`/
    `update_harness` take the id, `invoke_harness` takes the full ARN."""
    if not settings.BEDROCK_HARNESS_ARN:
        raise BedrockError("Bedrock is not configured (missing BEDROCK_HARNESS_ARN)")
    return settings.BEDROCK_HARNESS_ARN.rsplit("/", 1)[-1]


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
    """El id del modelo activo actualmente en el harness (lectura en vivo -
    el harness es la fuente de verdad, este servicio nunca lo guarda en
    caché)."""
    client = _get_control_client()

    def _get():
        return client.get_harness(harnessId=_harness_id())

    try:
        harness = await asyncio.to_thread(_get)
    except Exception as e:
        raise BedrockError(f"Failed to read current model: {e}") from e
    return harness["harness"]["model"]["bedrockModelConfig"]["modelId"]


async def switch_model(model_id: str) -> None:
    """Apunta el harness a otro modelo. `model_id` debe ser uno de
    `settings.BEDROCK_AVAILABLE_MODELS` - son los únicos cuyo acceso IAM (y,
    para modelos de Anthropic, el acuerdo de Marketplace) ya está
    aprovisionado; elegir un modelo arbitrario aquí solo fallaría con
    AccessDeniedException en el siguiente turno de chat."""
    if model_id not in settings.BEDROCK_AVAILABLE_MODELS:
        raise BedrockError(f"Model not in the allow-list: {model_id}")

    client = _get_control_client()

    def _update():
        return client.update_harness(
            harnessId=_harness_id(),
            model={"bedrockModelConfig": {"modelId": model_id, "apiFormat": "converse_stream"}},
        )

    try:
        await asyncio.to_thread(_update)
    except Exception as e:
        raise BedrockError(f"Failed to switch model: {e}") from e


# ---------------------------------------------------------------------------
# Memoria - vistas de solo lectura de lo que AgentCore Memory tiene
# guardado de un usuario. Las plantillas de namespace se confirmaron en
# vivo con `get_memory` contra la instancia real de memoria administrada
# (sus estrategias por default), no se adivinaron:
#   hechos semánticos:      /actors/{actorId}/facts/
#   resúmenes de sesión:    /actors/{actorId}/summaries/{sessionId}/
# ---------------------------------------------------------------------------

_memory_id: Optional[str] = None


async def _get_memory_id() -> str:
    """El id de la instancia de memoria administrada, leído una vez del
    harness y guardado en caché - a diferencia del modelo, esto no es algo
    que operaciones tipo switch_model cambien en tiempo de ejecución."""
    global _memory_id
    if _memory_id is not None:
        return _memory_id
    client = _get_control_client()

    def _get():
        return client.get_harness(harnessId=_harness_id())

    try:
        harness = await asyncio.to_thread(_get)
    except Exception as e:
        raise BedrockError(f"Failed to read memory id: {e}") from e
    arn = harness["harness"]["memory"]["managedMemoryConfiguration"]["arn"]
    _memory_id = arn.rsplit("/", 1)[-1]
    return _memory_id


async def list_memory_events(user_id: int, session_id: str, max_results: int = 50) -> List[Dict[str, Any]]:
    """Eventos crudos de memoria de corto plazo (mensajes, llamadas a
    herramientas) de una conversación - el registro técnico detrás de lo
    que `bedrockChatStore` ya muestra como burbujas de chat, útil para
    confirmar qué llegó realmente a la memoria del harness versus lo que
    renderiza la UI."""
    runtime = _get_runtime_client()
    memory_id = await _get_memory_id()

    def _list():
        return runtime.list_events(
            memoryId=memory_id,
            actorId=str(user_id),
            sessionId=session_id,
            maxResults=max_results,
            includePayloads=True,
        )

    try:
        response = await asyncio.to_thread(_list)
    except Exception as e:
        raise BedrockError(f"Failed to list memory events: {e}") from e
    return response.get("events", [])


async def retrieve_memory_records(user_id: int, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
    """Búsqueda semántica sobre los hechos durables que la estrategia
    SEMANTIC de AgentCore ha extraído de este usuario a través de todas sus
    conversaciones pasadas - esta es la vista de "qué recuerdas
    realmente de mí", distinta del registro crudo de eventos por sesión de
    arriba."""
    runtime = _get_runtime_client()
    memory_id = await _get_memory_id()

    def _retrieve():
        return runtime.retrieve_memory_records(
            memoryId=memory_id,
            namespace=f"/actors/{user_id}/facts/",
            searchCriteria={"searchQuery": query, "topK": top_k},
        )

    try:
        response = await asyncio.to_thread(_retrieve)
    except Exception as e:
        raise BedrockError(f"Failed to retrieve memory records: {e}") from e
    return response.get("memoryRecordSummaries", [])


async def create_manual_memory(user_id: int, text: str) -> None:
    """Siembra manualmente un hecho en la memoria de largo plazo del agente
    - Carlos diciéndole algo directamente, en vez de que se extraiga de una
    conversación real. Se escribe como un evento sintético con rol USER
    bajo un session id dedicado (para que no se mezcle con la transcripción
    cruda de ninguna conversación real); la estrategia SEMANTIC de
    AgentCore lo recoge de forma asíncrona igual que haría con un mensaje
    real, y queda disponible vía retrieve_memory_records una vez
    procesado."""
    import uuid
    from datetime import datetime, timezone

    runtime = _get_runtime_client()
    memory_id = await _get_memory_id()
    session_id = f"manual-memory-{uuid.uuid4().hex}"

    def _create():
        return runtime.create_event(
            memoryId=memory_id,
            actorId=str(user_id),
            sessionId=session_id,
            eventTimestamp=datetime.now(timezone.utc),
            payload=[{"conversational": {"content": {"text": text}, "role": "USER"}}],
        )

    try:
        await asyncio.to_thread(_create)
    except Exception as e:
        raise BedrockError(f"Failed to create manual memory: {e}") from e


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
                    "properties": {"resource_key": _RESOURCE_KEY_PARAM, "record_id": {"type": "integer"}},
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
                        "record_id": {"type": "integer"},
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
                    "properties": {"resource_key": _RESOURCE_KEY_PARAM, "record_id": {"type": "integer"}},
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


async def set_custom_tool_enabled(db, tool_id: int, is_enabled: bool) -> Optional["BedrockCustomTool"]:  # noqa: F821
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


async def delete_custom_tool(db, tool_id: int) -> bool:
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


async def _record_audit(
    db,
    *,
    user_id: int,
    action: str,
    resource_key: str,
    record_id: Optional[int],
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


async def _execute_tool(db, user_id: int, name: str, tool_input: Dict[str, Any], session_id: str) -> Dict[str, Any]:
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
        item = await repo.get_for_user(db, user_id, tool_input["record_id"])
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
        before = await repo.get_for_user(db, user_id, tool_input["record_id"])
        if before is None:
            return {"error": "not_found"}
        before_serialized = _serialize(before)
        item = await repo.update_for_user(db, user_id, tool_input["record_id"], tool_input["fields"])
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
        record_id = tool_input["record_id"]
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

async def list_audit_log(db, user_id: int, limit: int = 50, offset: int = 0) -> List["AuditLog"]:  # noqa: F821
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


async def restore_audit_entry(db, user_id: int, audit_id: int) -> Dict[str, Any]:
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
# Parseo de la respuesta en streaming + registro de costo -
# `invoke_harness` SIEMPRE devuelve un stream de eventos (nunca un JSON
# único, ni siquiera para una respuesta de puro texto sin uso de
# herramientas), porque así está diseñada la API de AgentCore Harness.
# `_consume_stream` es lo que convierte ese stream crudo de AWS en el dict
# simple que usa el resto de este módulo; `_record_usage` es un tema
# aparte (facturación) que solo lee su input del campo `usage` de ese mismo
# dict.
# ---------------------------------------------------------------------------


def _consume_stream(stream) -> Dict[str, Any]:
    """Drain one `invoke_harness` event stream into a plain result: the
    accumulated text, any tool-use blocks (keyed by content-block index, to
    stay correct if the model requests more than one tool in the same turn),
    the stop reason, and the token usage for this one call."""
    text = ""
    stop_reason: Optional[str] = None
    usage = {"inputTokens": 0, "outputTokens": 0}
    tool_uses: Dict[int, Dict[str, Any]] = {}

    for event in stream:
        index = event.get("contentBlockIndex")

        if "contentBlockStart" in event:
            start = event["contentBlockStart"].get("start", {})
            if "toolUse" in start:
                tool_uses[index] = {
                    "toolUseId": start["toolUse"]["toolUseId"],
                    "name": start["toolUse"]["name"],
                    "input_raw": "",
                }

        if "contentBlockDelta" in event:
            delta = event["contentBlockDelta"].get("delta", {})
            if "text" in delta:
                text += delta["text"]
            if "toolUse" in delta and index in tool_uses:
                tool_uses[index]["input_raw"] += delta["toolUse"].get("input", "")

        if "messageStop" in event:
            stop_reason = event["messageStop"].get("stopReason")

        if "metadata" in event:
            event_usage = event["metadata"].get("usage", {})
            usage["inputTokens"] += event_usage.get("inputTokens", 0)
            usage["outputTokens"] += event_usage.get("outputTokens", 0)

    parsed_tool_uses = []
    for tool_use in tool_uses.values():
        raw = tool_use.pop("input_raw")
        tool_use["input"] = json.loads(raw) if raw else {}
        parsed_tool_uses.append(tool_use)

    return {"text": text, "stop_reason": stop_reason, "usage": usage, "tool_uses": parsed_tool_uses}


async def _record_usage(user_id: int, session_id: str, model_id: str, usage: Dict[str, int]) -> None:
    """Best-effort: persist token usage for the cost dashboard. Never lets a
    logging failure fail the chat turn that already succeeded."""
    try:
        from database import AsyncSessionLocal
        from models.bedrock_usage_log import BedrockUsageLog

        pricing = settings.BEDROCK_AVAILABLE_MODELS.get(model_id, {})
        input_tokens = usage["inputTokens"]
        output_tokens = usage["outputTokens"]
        cost = (
            input_tokens * pricing.get("price_input_per_million", 0) / 1_000_000
            + output_tokens * pricing.get("price_output_per_million", 0) / 1_000_000
        )

        async with AsyncSessionLocal() as db:
            db.add(
                BedrockUsageLog(
                    user_id=user_id,
                    session_id=session_id,
                    model_id=model_id,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    estimated_cost_usd=cost,
                )
            )
            await db.commit()
    except Exception:
        logger.warning("Failed to record Bedrock usage log - continuing without it", exc_info=True)


# ---------------------------------------------------------------------------
# Conversaciones - historial guardado del lado del servidor, para que sea
# el mismo en cualquier dispositivo en vez de vivir en el localStorage de
# un solo navegador. El `session_id` de aquí es exactamente el mismo id que
# se le pasa a invoke_harness como runtimeSessionId (ver chat_stream) - una
# fila por conversación, no un segundo id que mantener sincronizado.
# ---------------------------------------------------------------------------

def _conversation_title_from(text: str) -> str:
    return text[:60] + "…" if len(text) > 60 else text


async def _get_or_create_conversation(db, user_id: int, session_id: str, first_message: str) -> "BedrockConversation":  # noqa: F821
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


async def list_conversations(db, user_id: int) -> List["BedrockConversation"]:  # noqa: F821
    from sqlalchemy import select

    from models.bedrock_conversation import BedrockConversation

    result = await db.execute(
        select(BedrockConversation)
        .where(BedrockConversation.user_id == user_id)
        .order_by(BedrockConversation.updated_at.desc())
    )
    return result.scalars().all()


async def get_conversation_messages(db, user_id: int, session_id: str) -> List["BedrockConversationMessage"]:  # noqa: F821
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


async def rename_conversation(db, user_id: int, session_id: str, title: str) -> bool:
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


async def delete_conversation(db, user_id: int, session_id: str) -> bool:
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


async def chat(db, user_id: int, session_id: str, message: str) -> Dict[str, Any]:
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


async def chat_stream(db, user_id: int, session_id: str, message: str):
    """Same turn as `chat`, but yields progress as it happens instead of
    only returning a final answer - a tool-use turn can take a while for
    real (AWS round trips, cold starts), and with nothing but a spinner
    that looks indistinguishable from actually being stuck. Yields
    `{"type": "status", "message": str}` before each tool call and
    `{"type": "done", "reply": str, "affected_resources": [...]}` at the end
    (or `{"type": "error", "message": str}` on failure - the route turns
    that into a terminal SSE event rather than raising mid-stream, since the
    HTTP response's headers/status are already committed by then).
    """
    # Paso 1 - reunir todo lo que este turno necesita ANTES de llamar a
    # AWS: qué cliente usar, qué modelo está activo (solo para el registro
    # de costo - el modelo ya viene incluido en el harness, ver
    # switch_model), la lista de herramientas actual (las propias + las
    # MCP habilitadas) y el system prompt activo (el override de Carlos o
    # el default). Todo se lee de nuevo en cada turno, nada queda en caché
    # salvo la conexión del cliente en sí.
    runtime = _get_runtime_client()
    harness_arn = settings.BEDROCK_HARNESS_ARN
    if not harness_arn:
        raise BedrockError("Bedrock is not configured (missing BEDROCK_HARNESS_ARN)")

    model_id = await get_current_model()
    tools = await _active_tools(db)
    system_prompt = await get_system_prompt(db)
    affected_resources: List[str] = []
    total_usage = {"inputTokens": 0, "outputTokens": 0}

    # Paso 2 - guardar el mensaje del usuario en NUESTRA PROPIA base de
    # datos (esto es distinto de AgentCore Memory, que el harness maneja
    # del lado de AWS solo para el recuerdo propio del modelo - esta copia
    # es lo que alimenta el "Historial de conversaciones" de la UI y hace
    # que sea igual en cualquier dispositivo). Se guarda al momento, no es
    # best-effort: perder el historial de chat en silencio es justo lo que
    # esto existe para evitar, así que un fallo aquí sí se muestra como un
    # error real a quien llamó.
    conversation = await _get_or_create_conversation(db, user_id, session_id, message)
    await _append_message(db, conversation, "user", message)

    # Paso 3 - este closure es LA llamada de red real a AWS: cada
    # `invoke_harness` de este turno (puede haber varias, una por cada
    # vuelta de uso de herramienta más abajo) pasa por aquí. Nota lo que
    # NO se envía: el historial completo de la conversación.
    # `runtimeSessionId=session_id` es lo que le dice al harness "esto es
    # continuación de la sesión X" - él busca e inyecta ese historial de su
    # lado, así que esta llamada solo lleva lo nuevo desde la anterior (el
    # mensaje del usuario la primera vez, y el resultado de una herramienta
    # en cada vuelta siguiente).
    def _invoke(messages: List[Dict[str, Any]]):
        return runtime.invoke_harness(
            harnessArn=harness_arn,
            runtimeSessionId=session_id,
            # Aísla AgentCore Memory por usuario real en vez del
            # "default_actor" compartido implícito - necesario para que el
            # visor de memoria por usuario (list_memory_events/
            # retrieve_memory_records más abajo) tenga sentido.
            actorId=str(user_id),
            tools=tools,
            systemPrompt=[{"text": system_prompt}],
            messages=messages,
        )

    # `next_messages` es lo que realmente entra a la SIGUIENTE llamada de
    # `_invoke` - empieza siendo solo el mensaje nuevo del usuario, y se
    # REEMPLAZA (no se le agrega) después de cada vuelta de uso de
    # herramienta, ya que el harness recuerda todo lo anterior vía
    # `runtimeSessionId`.
    next_messages: List[Dict[str, Any]] = [{"role": "user", "content": [{"text": message}]}]
    yield {"type": "status", "message": "Pensando..."}

    # Paso 4 - el loop de vueltas (round trips). Cada iteración es UNA
    # llamada a `invoke_harness`; el modelo puede pedir usar una o varias
    # herramientas, nosotros las ejecutamos localmente y le devolvemos el
    # resultado en la siguiente vuelta, hasta que responda con texto final
    # (`stop_reason != "tool_use"`) o se agote el límite de vueltas.
    #
    # 10, no 6: medido en la práctica, un create sobre un recurso poco
    # conocido puede tomar 4+ vueltas solo por prueba y error de nombres de
    # campo (ver describe_resource_schema/_invalid_fields_error, que
    # reducen esto pero no lo eliminan) - 6 era tan justo que a veces se
    # agotaba en una sola escritura que de otro modo hubiera funcionado.
    for _ in range(10):
        # Paso 4a - la llamada real (ver Paso 3) más el parseo del stream
        # de respuesta a un dict simple.
        try:
            response = await asyncio.to_thread(_invoke, next_messages)
            result = _consume_stream(response["stream"])
        except Exception as e:
            await _record_usage(user_id, session_id, model_id, total_usage)
            yield {"type": "error", "message": f"Bedrock request failed: {e}"}
            return

        total_usage["inputTokens"] += result["usage"]["inputTokens"]
        total_usage["outputTokens"] += result["usage"]["outputTokens"]

        # Paso 4b - salida normal: el modelo ya no pide más herramientas,
        # esto es la respuesta final. Se guarda en nuestra base de datos
        # (mismo motivo que el mensaje del usuario en el Paso 2) y se
        # entrega como evento "done" - aquí termina el turno.
        if result["stop_reason"] != "tool_use":
            await _record_usage(user_id, session_id, model_id, total_usage)
            await _append_message(db, conversation, "assistant", result["text"])
            yield {"type": "done", "reply": result["text"], "affected_resources": affected_resources}
            return

        # Paso 4c - el modelo pidió una o más herramientas. Primero se
        # avisa al frontend (evento "status") qué se está haciendo, para
        # que el usuario vea progreso real en vez de un spinner ciego.
        for t in result["tool_uses"]:
            yield {"type": "status", "message": _TOOL_STATUS_MESSAGES.get(t["name"], f"Usando {t['name']}...")}

        # Paso 4d - se ejecuta cada herramienta localmente (ver
        # `_execute_tool` arriba) y se arma el `toolResult` que AWS espera
        # como respuesta - un error de ejecución NO rompe el turno, se le
        # devuelve al modelo como resultado con status="error" para que
        # decida cómo seguir (reintentar con otros datos, avisarle a
        # Carlos, etc.).
        assistant_content = [
            {"toolUse": {"toolUseId": t["toolUseId"], "name": t["name"], "input": t["input"]}}
            for t in result["tool_uses"]
        ]
        tool_result_content = []
        for t in result["tool_uses"]:
            try:
                tool_result = await _execute_tool(db, user_id, t["name"], t["input"], session_id)
                status = "success"
                if t["name"] in _WRITE_TOOLS:
                    affected_resources.append(t["input"]["resource_key"])
            except Exception as e:
                tool_result = {"error": str(e)}
                status = "error"
            tool_result_content.append(
                {
                    "toolResult": {
                        "toolUseId": t["toolUseId"],
                        "content": [{"text": json.dumps(tool_result)}],
                        "status": status,
                    }
                }
            )

        # Paso 4e - se arma el mensaje para la SIGUIENTE vuelta: lo que el
        # modelo "dijo" (que pidió usar la herramienta) seguido de lo que
        # nosotros "respondemos" (el resultado) - el ciclo vuelve al Paso
        # 4a con esto como `next_messages`.
        next_messages = [
            {"role": "assistant", "content": assistant_content},
            {"role": "user", "content": tool_result_content},
        ]

    # Se agotaron las 10 vueltas sin que el modelo diera una respuesta
    # final - se registra el uso igual (para no perder el costo ya
    # incurrido) y se informa el error al frontend.
    await _record_usage(user_id, session_id, model_id, total_usage)
    yield {"type": "error", "message": "Too many tool-use round-trips without a final answer"}
