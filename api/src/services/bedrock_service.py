"""
Agent Bedrock - the Admin Panel's in-process AI assistant.

Per the project's architecture (docs/04-SOLUTION-STRATEGY.md Decisión 5,
docs/06-RUNTIME-VIEW.md Escenario 4): Bedrock has no container, no port, no
auth of its own - it's invoked in-process by the API REST, inheriting the
JWT of whichever Admin Panel session called it. This module is that
invocation, built on Amazon Bedrock AgentCore Harness (not a hand-rolled
Converse loop): `invoke_harness` handles the model call, tool-use
orchestration signaling and session memory server-side (keyed by
`runtimeSessionId`) - this module only needs to execute the `inline_function`
tools when the harness pauses for one, and feed the result back. The tools
themselves operate directly on `CareerRepository` (the exact same class
every generic CRUD route already uses) plus the Qdrant knowledge base
(`qdrant_service.py`).

The agent's capabilities - full read/write/create/delete on any of the
~30 career-domain resources, and semantic search over its knowledge base -
are a deliberate product decision (not something this module restricts):
every write goes straight through `CareerRepository`, no separate
"proposal" step.

Model switching: the model is not a per-invocation parameter, it's part of
the harness resource's own config. `switch_model` calls the control-plane
`UpdateHarness`, which creates a new immutable harness version and moves the
harness's DEFAULT endpoint to it - `get_current_model` always reflects the
live value by reading the harness back, rather than caching it locally,
since the harness itself is the single source of truth here.
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
# Model switching
# ---------------------------------------------------------------------------

async def get_current_model() -> str:
    """The model id currently active on the harness (read live - the harness
    itself is the source of truth, this service never caches it)."""
    client = _get_control_client()

    def _get():
        return client.get_harness(harnessId=_harness_id())

    try:
        harness = await asyncio.to_thread(_get)
    except Exception as e:
        raise BedrockError(f"Failed to read current model: {e}") from e
    return harness["harness"]["model"]["bedrockModelConfig"]["modelId"]


async def switch_model(model_id: str) -> None:
    """Point the harness at a different model. `model_id` must be one of
    `settings.BEDROCK_AVAILABLE_MODELS` - those are the only ones whose IAM
    access (and, for Anthropic models, Marketplace agreement) has already
    been provisioned; picking an arbitrary model here would just fail with
    AccessDeniedException on the next chat turn."""
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
# Memory - read-only views into what AgentCore Memory has stored for a user.
# Namespace templates confirmed live via `get_memory` against the real
# managed memory instance (its default strategies), not guessed:
#   semantic facts:   /actors/{actorId}/facts/
#   session summaries: /actors/{actorId}/summaries/{sessionId}/
# ---------------------------------------------------------------------------

_memory_id: Optional[str] = None


async def _get_memory_id() -> str:
    """The managed memory instance's id, read once from the harness and
    cached - unlike the model, this isn't something switch_model-style
    operations change at runtime."""
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
    """Raw short-term memory events (messages, tool calls) for one
    conversation - the technical record behind what `bedrockChatStore`
    already shows as chat bubbles, useful to confirm what actually made it
    into the harness's memory versus what the UI renders."""
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
    """Semantic search over the durable facts AgentCore's SEMANTIC strategy
    has extracted about this user across every past conversation - this is
    the "what do you actually remember about me" view, distinct from the
    raw per-session event log above."""
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
    """Manually seed a fact into the agent's long-term memory - Carlos
    telling it something directly, rather than it being extracted from a
    real conversation. Written as a synthetic USER-role event under a
    dedicated session id (so it doesn't get mixed into any real
    conversation's raw transcript); AgentCore's SEMANTIC strategy picks it
    up asynchronously the same way it would a real message, and it becomes
    retrievable via retrieve_memory_records once processed."""
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
# Tools exposed to the harness (inline_function tools)
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
    """Built-in tools plus every enabled `BedrockCustomTool` (MCP servers
    Carlos registered from the app - see routes/bedrock.py's /tools
    endpoints), as `remote_mcp` tool entries. This is how new capabilities
    get added without a code deploy: register an MCP server URL, its tools
    are available on the next turn."""
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
# Audit log - read + restore. Writing happens in _execute_tool/_record_audit
# above; this is Carlos's side of it (Bitácora page).
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
    """Undo a delete the agent made: re-creates the record from the audit
    entry's `old_values` (the full row captured right before the delete).
    Only meaningful for `delete` entries - a create/update has nothing to
    "restore" to that isn't already the current row."""
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
# Conversations - server-side history, so it's the same on every device
# instead of living in one browser's localStorage. `session_id` here is the
# exact same id passed to invoke_harness as runtimeSessionId (see
# chat_stream) - one row per conversation, not a second id to keep in sync.
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
    runtime = _get_runtime_client()
    harness_arn = settings.BEDROCK_HARNESS_ARN
    if not harness_arn:
        raise BedrockError("Bedrock is not configured (missing BEDROCK_HARNESS_ARN)")

    model_id = await get_current_model()
    tools = await _active_tools(db)
    system_prompt = await get_system_prompt(db)
    affected_resources: List[str] = []
    total_usage = {"inputTokens": 0, "outputTokens": 0}

    # Server-side conversation history (so it's the same from any device -
    # see models/bedrock_conversation.py). Saved as-you-go, not best-effort:
    # losing chat history silently is exactly the kind of thing this exists
    # to prevent, so a failure here surfaces as a real error to the caller.
    conversation = await _get_or_create_conversation(db, user_id, session_id, message)
    await _append_message(db, conversation, "user", message)

    def _invoke(messages: List[Dict[str, Any]]):
        return runtime.invoke_harness(
            harnessArn=harness_arn,
            runtimeSessionId=session_id,
            # Scopes AgentCore Memory per real user instead of the implicit
            # shared "default_actor" - required for the per-user memory
            # viewer (list_memory_events/retrieve_memory_records below) to
            # mean anything.
            actorId=str(user_id),
            tools=tools,
            systemPrompt=[{"text": system_prompt}],
            messages=messages,
        )

    next_messages: List[Dict[str, Any]] = [{"role": "user", "content": [{"text": message}]}]
    yield {"type": "status", "message": "Pensando..."}

    # 10, not 6: measured for real, a create on an unfamiliar resource can
    # take 4+ round trips just from field-name trial and error (see
    # describe_resource_schema/_invalid_fields_error, which cut that down
    # but don't eliminate it) - 6 was tight enough to occasionally exhaust
    # itself on a single, otherwise-successful write.
    for _ in range(10):
        try:
            response = await asyncio.to_thread(_invoke, next_messages)
            result = _consume_stream(response["stream"])
        except Exception as e:
            await _record_usage(user_id, session_id, model_id, total_usage)
            yield {"type": "error", "message": f"Bedrock request failed: {e}"}
            return

        total_usage["inputTokens"] += result["usage"]["inputTokens"]
        total_usage["outputTokens"] += result["usage"]["outputTokens"]

        if result["stop_reason"] != "tool_use":
            await _record_usage(user_id, session_id, model_id, total_usage)
            await _append_message(db, conversation, "assistant", result["text"])
            yield {"type": "done", "reply": result["text"], "affected_resources": affected_resources}
            return

        for t in result["tool_uses"]:
            yield {"type": "status", "message": _TOOL_STATUS_MESSAGES.get(t["name"], f"Usando {t['name']}...")}

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

        next_messages = [
            {"role": "assistant", "content": assistant_content},
            {"role": "user", "content": tool_result_content},
        ]

    await _record_usage(user_id, session_id, model_id, total_usage)
    yield {"type": "error", "message": "Too many tool-use round-trips without a final answer"}
