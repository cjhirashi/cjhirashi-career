"""
Proveedor Bedrock: Converse / ConverseStream con tool calling y prompt caching.

Traslado, con paridad de comportamiento (D-13), de `cjhirashi-career-api/src/services/bedrock/
converse_client.py`: construcción del payload con hasta 3 `cachePoint` (ADR-019), Converse o
ConverseStream según `BEDROCK_USE_CONVERSE_STREAM` con respaldo a Converse ante
AccessDeniedException, y traducción de errores de botocore a `BedrockError`.
Sin `report_error`: el reporte de errores del harness (services/error_reporting) llega en el Bloque E/F.
"""
import asyncio
import json
import logging
from typing import Any, AsyncIterator, Dict, List, Optional

from botocore.exceptions import ClientError

from providers.base import (
    ImageOptions,
    ImageResult,
    ModelInfo,
    ModelRequest,
    ModelResponse,
    StreamEvent,
    ToolCall,
    ToolSpec,
    Usage,
)
from providers.bedrock import client as client_mod
from providers.bedrock import images
from providers.bedrock import pricing
from providers.bedrock.errors import BedrockError, format_bedrock_client_error
from providers.reply_text import sanitize_assistant_reply

logger = logging.getLogger(__name__)


# ============================================================================
# Payload
# ============================================================================

def cache_point() -> Dict[str, Any]:
    """Bloque cachePoint fresco (nunca compartir la misma instancia entre payloads)."""
    return {"cachePoint": {"type": "default"}}


def _tool_to_wire(tool: ToolSpec) -> Dict[str, Any]:
    return {
        "toolSpec": {
            "name": tool.name,
            "description": tool.description,
            "inputSchema": {"json": tool.input_schema},
        }
    }


def build_converse_kwargs(
    settings: Any,
    *,
    model_id: str,
    messages: List[Dict[str, Any]],
    system_prompt: str,
    tools: List[ToolSpec],
    max_tokens: int,
    force_tool_use: bool,
) -> Dict[str, Any]:
    """Arma el payload de Converse; inserta hasta 3 cachePoint si el modelo lo soporta.

    Los cachePoint van al final de `system`, al final de `toolConfig.tools` y al
    final del `content` del último mensaje (prefijo estable ronda a ronda). El
    último se hace sobre una copia superficial para no mutar `messages`, que
    el bucle de agente sigue extendiendo entre rondas."""
    cache = bool(settings.BEDROCK_PROMPT_CACHE_ENABLED) and pricing.supports_prompt_cache(model_id)

    system_blocks: List[Dict[str, Any]] = [{"text": system_prompt}]
    if cache:
        system_blocks.append(cache_point())

    api_messages = messages
    if cache and messages:
        last = dict(messages[-1])
        last["content"] = list(last.get("content") or []) + [cache_point()]
        api_messages = messages[:-1] + [last]

    kwargs: Dict[str, Any] = {
        "modelId": model_id,
        "messages": api_messages,
        "system": system_blocks,
        "inferenceConfig": {"maxTokens": max_tokens},
    }
    wire_tools = [_tool_to_wire(t) for t in tools]
    if wire_tools:
        tool_list = (wire_tools + [cache_point()]) if cache else wire_tools
        kwargs["toolConfig"] = {"tools": tool_list}
        if force_tool_use:
            kwargs["toolConfig"]["toolChoice"] = {"any": {}}
    return kwargs


# ============================================================================
# Respuesta
# ============================================================================

def _usage_from(raw: Dict[str, Any]) -> Usage:
    return Usage(
        input_tokens=raw.get("inputTokens", 0),
        output_tokens=raw.get("outputTokens", 0),
        # Bedrock reporta los tokens de caché aparte; inputTokens ya viene sin ellos.
        cache_read_tokens=raw.get("cacheReadInputTokens", 0) or 0,
        cache_write_tokens=raw.get("cacheWriteInputTokens", 0) or 0,
    )


def parse_converse_response(response: Dict[str, Any]) -> ModelResponse:
    """Normaliza la respuesta de Converse (no streaming) al formato neutro."""
    content = response.get("output", {}).get("message", {}).get("content", [])
    text_parts: List[str] = []
    calls: List[ToolCall] = []
    for block in content:
        # reasoningContent (DeepSeek / Claude extended thinking) es interno y nunca
        # se concatena a la respuesta visible.
        if "text" in block:
            text_parts.append(block["text"])
        if "toolUse" in block:
            tu = block["toolUse"]
            calls.append(ToolCall(id=tu["toolUseId"], name=tu["name"], input=tu.get("input") or {}))
    return ModelResponse(
        text=sanitize_assistant_reply("".join(text_parts)),
        stop_reason=response.get("stopReason"),
        usage=_usage_from(response.get("usage", {})),
        tool_calls=calls,
    )


def _finish_tool_call(tu: Dict[str, Any]) -> ToolCall:
    raw = tu["input_raw"]
    try:
        return ToolCall(id=tu["id"], name=tu["name"], input=json.loads(raw) if raw else {})
    except json.JSONDecodeError as exc:
        logger.warning("Invalid JSON in streamed tool input name=%s: %s", tu.get("name"), exc)
        return ToolCall(
            id=tu["id"],
            name=tu["name"],
            input={},
            input_parse_error=(
                f"Invalid JSON in tool arguments ({exc}). "
                "Retry with valid JSON; escape quotes and newlines in Markdown."
            ),
        )


def _block_index(event: Dict[str, Any], key: str) -> int:
    """Índice del bloque de contenido. En la API real `contentBlockIndex` va DENTRO de
    contentBlockStart/Delta/Stop (modelo de servicio de botocore); la API origen lo leía
    del nivel superior (siempre 0), lo que mezclaba varios tool_use en uno. Se lee el
    interno y se conserva el nivel superior como respaldo."""
    inner = event.get(key, {}).get("contentBlockIndex")
    return inner if inner is not None else event.get("contentBlockIndex", 0)


def consume_converse_stream(stream) -> ModelResponse:
    """Convierte el stream Converse en texto, tool_calls, stop_reason y usage."""
    text = ""
    stop_reason: Optional[str] = None
    usage = Usage()
    tool_uses: Dict[int, Dict[str, Any]] = {}

    for event in stream:
        if "contentBlockStart" in event:
            start = event["contentBlockStart"].get("start", {})
            idx = _block_index(event, "contentBlockStart")
            if "toolUse" in start:
                tool_uses[idx] = {
                    "id": start["toolUse"]["toolUseId"],
                    "name": start["toolUse"]["name"],
                    "input_raw": "",
                }
        if "contentBlockDelta" in event:
            delta = event["contentBlockDelta"].get("delta", {})
            idx = _block_index(event, "contentBlockDelta")
            if "text" in delta:
                text += delta["text"]
            if "toolUse" in delta and idx in tool_uses:
                tool_uses[idx]["input_raw"] += delta["toolUse"].get("input", "")
        if "messageStop" in event:
            stop_reason = event["messageStop"].get("stopReason")
        if "metadata" in event:
            u = _usage_from(event["metadata"].get("usage", {}))
            usage.input_tokens += u.input_tokens
            usage.output_tokens += u.output_tokens
            usage.cache_read_tokens += u.cache_read_tokens
            usage.cache_write_tokens += u.cache_write_tokens

    return ModelResponse(
        text=sanitize_assistant_reply(text),
        stop_reason=stop_reason,
        usage=usage,
        tool_calls=[_finish_tool_call(tu) for tu in tool_uses.values()],
    )


def iter_stream_events(stream) -> "Iterator[StreamEvent]":  # noqa: F821
    """Traduce los eventos crudos de ConverseStream a `StreamEvent` neutros (síncrono)."""
    pending: Dict[int, Dict[str, Any]] = {}
    for event in stream:
        if "contentBlockStart" in event:
            start = event["contentBlockStart"].get("start", {})
            idx = _block_index(event, "contentBlockStart")
            if "toolUse" in start:
                pending[idx] = {"id": start["toolUse"]["toolUseId"], "name": start["toolUse"]["name"], "input_raw": ""}
        if "contentBlockDelta" in event:
            delta = event["contentBlockDelta"].get("delta", {})
            if "text" in delta:
                yield StreamEvent(kind="text", text=delta["text"])
            idx = _block_index(event, "contentBlockDelta")
            if "toolUse" in delta and idx in pending:
                pending[idx]["input_raw"] += delta["toolUse"].get("input", "")
        if "contentBlockStop" in event:
            stop_idx = _block_index(event, "contentBlockStop")
            if stop_idx in pending:
                yield StreamEvent(kind="tool_call", tool_call=_finish_tool_call(pending.pop(stop_idx)))
        if "messageStop" in event:
            yield StreamEvent(kind="stop", stop_reason=event["messageStop"].get("stopReason"))
        if "metadata" in event:
            yield StreamEvent(kind="usage", usage=_usage_from(event["metadata"].get("usage", {})))
    for tu in pending.values():  # bloques sin contentBlockStop (stream cortado)
        yield StreamEvent(kind="tool_call", tool_call=_finish_tool_call(tu))


# ============================================================================
# Proveedor
# ============================================================================

class BedrockProvider:
    """`ModelProvider` sobre Bedrock Runtime. Los clientes boto3 se inyectan en tests (stub)."""

    def __init__(self, settings: Any, runtime_client: Any = None, image_client: Any = None):
        self._settings = settings
        self._runtime_client = runtime_client
        self._image_client = image_client

    def _runtime(self) -> Any:
        if self._runtime_client is None:
            return client_mod.get_runtime_client(self._settings)
        return self._runtime_client

    def _image(self) -> Any:
        if self._image_client is None:
            return client_mod.get_image_client(self._settings)
        return self._image_client

    def _kwargs(self, request: ModelRequest) -> Dict[str, Any]:
        return build_converse_kwargs(
            self._settings,
            model_id=request.model_id,
            messages=request.messages,
            system_prompt=request.system_prompt,
            tools=request.tools,
            max_tokens=request.max_tokens,
            force_tool_use=request.force_tool_use,
        )

    @staticmethod
    def _wrap(exc: Exception, model_id: str, stage: Optional[str] = None) -> BedrockError:
        logger.error("Converse failed model=%s stage=%s", model_id, stage or "main", exc_info=exc)
        return BedrockError(format_bedrock_client_error(exc, model_id=model_id))

    async def converse(self, request: ModelRequest) -> ModelResponse:
        """Una llamada Converse en thread pool (ConverseStream si está habilitado)."""
        client = self._runtime()
        kwargs = self._kwargs(request)
        model_id = request.model_id
        use_stream = bool(self._settings.BEDROCK_USE_CONVERSE_STREAM)

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
                    raise self._wrap(fallback_err, model_id, "fallback") from fallback_err
            raise self._wrap(e, model_id) from e
        except Exception as e:
            raise self._wrap(e, model_id) from e

    async def converse_stream(self, request: ModelRequest) -> AsyncIterator[StreamEvent]:
        """ConverseStream como eventos neutros (texto, tool_call, stop, usage)."""
        client = self._runtime()
        kwargs = self._kwargs(request)
        try:
            response = await asyncio.to_thread(lambda: client.converse_stream(**kwargs))
            events = iter_stream_events(response["stream"])
            sentinel = object()
            while True:
                item = await asyncio.to_thread(next, events, sentinel)
                if item is sentinel:
                    return
                yield item
        except Exception as e:
            raise self._wrap(e, request.model_id, "stream") from e

    async def generate_image(self, prompt: str, options: ImageOptions) -> ImageResult:
        return ImageResult(data=await images.generate_image_bytes(self._image(), self._settings, prompt, options))

    def list_models(self) -> List[ModelInfo]:
        return pricing.list_models()

    def estimate_cost(self, model_id: str, usage: Usage) -> float:
        return pricing.estimate_cost(model_id, usage)
