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
# Tools exposed to the harness (inline_function tools)
# ---------------------------------------------------------------------------

_RESOURCE_KEY_PARAM = {
    "type": "string",
    "description": "The resource key, e.g. 'vacancies', 'projects', 'operational-methodologies'.",
}

TOOLS = [
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


async def _execute_tool(db, user_id: int, name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
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

    if name == "create_career_record":
        repo = _get_repository(tool_input["resource_key"])
        item = await repo.create_for_user(db, user_id, tool_input["fields"])
        return {"item": _serialize(item)}

    if name == "update_career_record":
        repo = _get_repository(tool_input["resource_key"])
        item = await repo.update_for_user(db, user_id, tool_input["record_id"], tool_input["fields"])
        if item is None:
            return {"error": "not_found"}
        return {"item": _serialize(item)}

    if name == "delete_career_record":
        repo = _get_repository(tool_input["resource_key"])
        deleted = await repo.delete_for_user(db, user_id, tool_input["record_id"])
        return {"deleted": deleted}

    raise BedrockError(f"Unknown tool: {name}")


def _system_prompt() -> str:
    resource_list = ", ".join(sorted(RESOURCE_REGISTRY.keys()))
    return (
        "Eres el asistente de carrera dentro del Admin Panel de Carlos Jiménez Hirashi. "
        "Tienes acceso completo de lectura y escritura sobre sus datos de carrera a través de tus "
        "herramientas - puedes listar, obtener, crear, actualizar y eliminar registros directamente, "
        "sin pedir confirmación adicional del sistema (Carlos ya te la dio al usarte). "
        "Antes de operar una tabla que no conozcas bien, usa search_knowledge_base para consultar la "
        "metodología operativa correspondiente - ahí está documentado cómo se relacionan las tablas "
        "entre sí y qué disciplina seguir en cada una. "
        "Responde siempre en español, de forma clara y directa sobre qué hiciste. "
        f"Recursos disponibles (resource_key): {resource_list}."
    )


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


async def chat(db, user_id: int, session_id: str, message: str) -> Dict[str, Any]:
    """Run one chat turn against the harness. The harness owns the
    conversation history server-side (keyed by `session_id`) - callers only
    ever send the newest user message, never the full history.

    Returns `{"reply": str, "affected_resources": list[str]}` -
    `affected_resources` lists every resource_key touched by a write tool
    this turn, so the frontend can invalidate its cache for those tables.
    """
    runtime = _get_runtime_client()
    harness_arn = settings.BEDROCK_HARNESS_ARN
    if not harness_arn:
        raise BedrockError("Bedrock is not configured (missing BEDROCK_HARNESS_ARN)")

    model_id = await get_current_model()
    affected_resources: List[str] = []
    total_usage = {"inputTokens": 0, "outputTokens": 0}

    def _invoke(messages: List[Dict[str, Any]]):
        return runtime.invoke_harness(
            harnessArn=harness_arn,
            runtimeSessionId=session_id,
            tools=TOOLS,
            messages=messages,
        )

    next_messages: List[Dict[str, Any]] = [{"role": "user", "content": [{"text": message}]}]

    for _ in range(6):
        try:
            response = await asyncio.to_thread(_invoke, next_messages)
            result = _consume_stream(response["stream"])
        except Exception as e:
            await _record_usage(user_id, session_id, model_id, total_usage)
            raise BedrockError(f"Bedrock request failed: {e}") from e

        total_usage["inputTokens"] += result["usage"]["inputTokens"]
        total_usage["outputTokens"] += result["usage"]["outputTokens"]

        if result["stop_reason"] != "tool_use":
            await _record_usage(user_id, session_id, model_id, total_usage)
            return {"reply": result["text"], "affected_resources": affected_resources}

        assistant_content = [
            {"toolUse": {"toolUseId": t["toolUseId"], "name": t["name"], "input": t["input"]}}
            for t in result["tool_uses"]
        ]
        tool_result_content = []
        for t in result["tool_uses"]:
            try:
                tool_result = await _execute_tool(db, user_id, t["name"], t["input"])
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
    raise BedrockError("Too many tool-use round-trips without a final answer")
