"""
Cliente ConverseStream — inferencia Bedrock con tool calling.

Cliente ConverseStream — inferencia Bedrock con tool calling (bedrock-runtime).
Ver api/docs/BEDROCK-HARNESS.md.
"""
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

from config import settings
from services.errors import BedrockError, format_bedrock_client_error
from services.reply_text import sanitize_assistant_reply
from services.error_reporting import report_error

logger = logging.getLogger(__name__)

_runtime_client = None


def _cache_point() -> Dict[str, Any]:
    """Bloque cachePoint fresco (nunca compartir la misma instancia entre payloads)."""
    return {"cachePoint": {"type": "default"}}


def _supports_prompt_cache(model_id: str) -> bool:
    """True si el modelo admite cachePoint y el kill-switch global está activo."""
    if not settings.BEDROCK_PROMPT_CACHE_ENABLED:
        return False
    return bool(
        settings.BEDROCK_AVAILABLE_MODELS.get(model_id, {}).get("supports_prompt_cache", False)
    )


# ============================================================================
# Cliente Bedrock Runtime
# ============================================================================

def _get_runtime_client():
    global _runtime_client
    if _runtime_client is None:
        if not settings.AWS_ACCESS_KEY_ID:
            raise BedrockError("Missing AWS credentials")
        _runtime_client = boto3.client(
            "bedrock-runtime",
            region_name=settings.BEDROCK_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
    return _runtime_client


# ============================================================================
# Respuesta Converse y tool use
# ============================================================================

def parse_converse_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """Normaliza la respuesta de Converse (no streaming) al formato interno del harness."""
    message = response.get("output", {}).get("message", {})
    content = message.get("content", [])
    text_parts: List[str] = []
    tool_uses: List[Dict[str, Any]] = []

    for block in content:
        # reasoningContent (DeepSeek / Claude extended thinking) is internal
        # and must never be concatenated into the user-facing reply.
        if "text" in block:
            text_parts.append(block["text"])
        if "toolUse" in block:
            tu = block["toolUse"]
            tool_uses.append(
                {
                    "toolUseId": tu["toolUseId"],
                    "name": tu["name"],
                    "input": tu.get("input") or {},
                }
            )

    usage = response.get("usage", {})
    return {
        "text": sanitize_assistant_reply("".join(text_parts)),
        "stop_reason": response.get("stopReason"),
        "usage": {
            "inputTokens": usage.get("inputTokens", 0),
            "outputTokens": usage.get("outputTokens", 0),
            # Bedrock reporta los tokens de caché aparte; inputTokens ya viene sin ellos.
            "cacheReadInputTokens": usage.get("cacheReadInputTokens", 0) or 0,
            "cacheWriteInputTokens": usage.get("cacheWriteInputTokens", 0) or 0,
        },
        "tool_uses": tool_uses,
    }


# ============================================================================
# Streaming Converse
# ============================================================================

def consume_converse_stream(stream) -> Dict[str, Any]:
    """Convierte el stream Converse en texto, tool_uses, stop_reason y usage."""
    text = ""
    stop_reason: Optional[str] = None
    usage = {
        "inputTokens": 0,
        "outputTokens": 0,
        "cacheReadInputTokens": 0,
        "cacheWriteInputTokens": 0,
    }
    tool_uses: Dict[int, Dict[str, Any]] = {}

    for event in stream:
        if "contentBlockStart" in event:
            start = event["contentBlockStart"].get("start", {})
            idx = event.get("contentBlockIndex", 0)
            if "toolUse" in start:
                tool_uses[idx] = {
                    "toolUseId": start["toolUse"]["toolUseId"],
                    "name": start["toolUse"]["name"],
                    "input_raw": "",
                }
        if "contentBlockDelta" in event:
            delta = event["contentBlockDelta"].get("delta", {})
            idx = event.get("contentBlockIndex", 0)
            if "text" in delta:
                text += delta["text"]
            if "toolUse" in delta and idx in tool_uses:
                tool_uses[idx]["input_raw"] += delta["toolUse"].get("input", "")
        if "messageStop" in event:
            stop_reason = event["messageStop"].get("stopReason")
        if "metadata" in event:
            u = event["metadata"].get("usage", {})
            usage["inputTokens"] += u.get("inputTokens", 0)
            usage["outputTokens"] += u.get("outputTokens", 0)
            usage["cacheReadInputTokens"] += u.get("cacheReadInputTokens", 0) or 0
            usage["cacheWriteInputTokens"] += u.get("cacheWriteInputTokens", 0) or 0

    parsed = []
    for tu in tool_uses.values():
        raw = tu.pop("input_raw", "")
        try:
            tu["input"] = json.loads(raw) if raw else {}
        except json.JSONDecodeError as exc:
            logger.warning("Invalid JSON in streamed tool input name=%s: %s", tu.get("name"), exc)
            tu["input"] = {}
            tu["input_parse_error"] = (
                f"Invalid JSON in tool arguments ({exc}). "
                "Retry with valid JSON; escape quotes and newlines in Markdown."
            )
        parsed.append(tu)

    return {
        "text": sanitize_assistant_reply(text),
        "stop_reason": stop_reason,
        "usage": usage,
        "tool_uses": parsed,
    }


# ============================================================================
# Invocación Converse
# ============================================================================

def _build_converse_kwargs(
    *,
    model_id: str,
    messages: List[Dict[str, Any]],
    system_prompt: str,
    tools: List[Dict[str, Any]],
    max_tokens: int,
    force_tool_use: bool,
) -> Dict[str, Any]:
    """Arma el payload de Converse; inserta hasta 3 cachePoint si el modelo lo soporta.

    Los cachePoint van al final de `system`, al final de `toolConfig.tools` y al
    final del `content` del último mensaje (prefijo estable ronda a ronda). El
    último se hace sobre una copia superficial para no mutar `messages`, que
    agent_loop sigue extendiendo entre rondas."""
    cache = _supports_prompt_cache(model_id)

    system_blocks: List[Dict[str, Any]] = [{"text": system_prompt}]
    if cache:
        system_blocks.append(_cache_point())

    api_messages = messages
    if cache and messages:
        last = dict(messages[-1])
        last["content"] = list(last.get("content") or []) + [_cache_point()]
        api_messages = messages[:-1] + [last]

    kwargs: Dict[str, Any] = {
        "modelId": model_id,
        "messages": api_messages,
        "system": system_blocks,
        "inferenceConfig": {"maxTokens": max_tokens},
    }
    if tools:
        tool_list = (list(tools) + [_cache_point()]) if cache else tools
        kwargs["toolConfig"] = {"tools": tool_list}
        if force_tool_use:
            kwargs["toolConfig"]["toolChoice"] = {"any": {}}
    return kwargs


async def converse(
    *,
    model_id: str,
    messages: List[Dict[str, Any]],
    system_prompt: str,
    tools: List[Dict[str, Any]],
    max_tokens: int = 4096,
    force_tool_use: bool = False,
) -> Dict[str, Any]:
    """Una llamada Converse en thread pool (ConverseStream si está habilitado)."""
    client = _get_runtime_client()
    kwargs = _build_converse_kwargs(
        model_id=model_id,
        messages=messages,
        system_prompt=system_prompt,
        tools=tools,
        max_tokens=max_tokens,
        force_tool_use=force_tool_use,
    )

    use_stream = settings.BEDROCK_USE_CONVERSE_STREAM

    def _call_stream():
        return client.converse_stream(**kwargs)

    def _call_sync():
        return client.converse(**kwargs)

    try:
        if use_stream:
            response = await asyncio.to_thread(_call_stream)
            return consume_converse_stream(response["stream"])

        response = await asyncio.to_thread(_call_sync)
        return parse_converse_response(response)
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        if use_stream and code == "AccessDeniedException":
            logger.warning(
                "ConverseStream denied (missing bedrock:InvokeModelWithResponseStream?), "
                "falling back to Converse model=%s",
                model_id,
            )
            try:
                response = await asyncio.to_thread(_call_sync)
                return parse_converse_response(response)
            except Exception as fallback_err:
                logger.exception("Converse fallback failed model=%s", model_id)
                report_error(
                    str(fallback_err), "bedrock:converse", error_type=type(fallback_err).__name__,
                    exc=fallback_err, context={"model_id": model_id, "stage": "fallback"}, severity="error",
                )
                raise BedrockError(format_bedrock_client_error(fallback_err, model_id=model_id)) from fallback_err
        logger.exception("Converse failed model=%s", model_id)
        report_error(
            str(e), "bedrock:converse", error_type=type(e).__name__,
            exc=e, context={"model_id": model_id}, severity="error",
        )
        raise BedrockError(format_bedrock_client_error(e, model_id=model_id)) from e
    except Exception as e:
        logger.exception("Converse failed model=%s", model_id)
        report_error(
            str(e), "bedrock:converse", error_type=type(e).__name__,
            exc=e, context={"model_id": model_id}, severity="error",
        )
        raise BedrockError(format_bedrock_client_error(e, model_id=model_id)) from e
