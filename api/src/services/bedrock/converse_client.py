"""
Cliente ConverseStream — inferencia Bedrock con tool calling.

Única capa que habla con bedrock-runtime Converse (no AgentCore Harness).
Ver api/docs/BEDROCK-HARNESS.md.
"""
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

import boto3

from config import settings
from services.bedrock.errors import BedrockError

logger = logging.getLogger(__name__)

_runtime_client = None


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


def consume_converse_stream(stream) -> Dict[str, Any]:
    """Convierte el stream Converse en texto, tool_uses, stop_reason y usage."""
    text = ""
    stop_reason: Optional[str] = None
    usage = {"inputTokens": 0, "outputTokens": 0}
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

    parsed = []
    for tu in tool_uses.values():
        raw = tu.pop("input_raw", "")
        try:
            tu["input"] = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            tu["input"] = {}
        parsed.append(tu)

    return {"text": text, "stop_reason": stop_reason, "usage": usage, "tool_uses": parsed}


async def converse(
    *,
    model_id: str,
    messages: List[Dict[str, Any]],
    system_prompt: str,
    tools: List[Dict[str, Any]],
    max_tokens: int = 4096,
) -> Dict[str, Any]:
    """Una llamada ConverseStream síncrona en thread pool."""
    client = _get_runtime_client()
    kwargs: Dict[str, Any] = {
        "modelId": model_id,
        "messages": messages,
        "system": [{"text": system_prompt}],
        "inferenceConfig": {"maxTokens": max_tokens},
    }
    if tools:
        kwargs["toolConfig"] = {"tools": tools}

    def _call():
        return client.converse_stream(**kwargs)

    try:
        response = await asyncio.to_thread(_call)
        return consume_converse_stream(response["stream"])
    except Exception as e:
        logger.exception("ConverseStream failed model=%s", model_id)
        raise BedrockError(f"Converse request failed: {e}") from e
