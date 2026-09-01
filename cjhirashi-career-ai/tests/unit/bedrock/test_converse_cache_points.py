"""Inserción de cachePoint en el payload de Converse, según soporte del modelo."""
from config import settings
from services.bedrock.converse_client import _build_converse_kwargs, _supports_prompt_cache

CACHED_MODEL = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
PLAIN_MODEL = "amazon.nova-lite-v1:0"  # en catálogo, sin supports_prompt_cache

_MESSAGES = [
    {"role": "user", "content": [{"text": "Hola"}]},
    {"role": "assistant", "content": [{"text": "Hola, ¿en qué ayudo?"}]},
]
_TOOLS = [{"toolSpec": {"name": "get_career_record", "inputSchema": {"json": {}}}}]


def _kwargs(model_id):
    return _build_converse_kwargs(
        model_id=model_id,
        messages=[{"role": m["role"], "content": list(m["content"])} for m in _MESSAGES],
        system_prompt="Eres un asistente.",
        tools=list(_TOOLS),
        max_tokens=1024,
        force_tool_use=False,
    )


def test_supported_model_gets_three_cache_points():
    k = _kwargs(CACHED_MODEL)
    assert k["system"][-1] == {"cachePoint": {"type": "default"}}
    assert k["toolConfig"]["tools"][-1] == {"cachePoint": {"type": "default"}}
    assert k["messages"][-1]["content"][-1] == {"cachePoint": {"type": "default"}}


def test_unsupported_model_gets_no_cache_points():
    k = _kwargs(PLAIN_MODEL)
    assert all("cachePoint" not in b for b in k["system"])
    assert all("cachePoint" not in b for b in k["toolConfig"]["tools"])
    for msg in k["messages"]:
        assert all("cachePoint" not in b for b in msg["content"])


def test_kill_switch_disables_cache(monkeypatch):
    monkeypatch.setattr(settings, "BEDROCK_PROMPT_CACHE_ENABLED", False)
    assert _supports_prompt_cache(CACHED_MODEL) is False
    k = _kwargs(CACHED_MODEL)
    assert all("cachePoint" not in b for b in k["system"])


def test_original_messages_not_mutated():
    original = [{"role": "user", "content": [{"text": "Hola"}]}]
    snapshot = [{"role": "user", "content": [{"text": "Hola"}]}]
    _build_converse_kwargs(
        model_id=CACHED_MODEL,
        messages=original,
        system_prompt="x",
        tools=[],
        max_tokens=16,
        force_tool_use=False,
    )
    assert original == snapshot
