"""RF-005: proveedor Bedrock — Converse, cachePoint, errores, costes (T-023).

Sin red ni AWS: `botocore.stub.Stubber` sobre un cliente boto3 real con credenciales falsas
(valida la petición contra el modelo de servicio de botocore) y dobles para el streaming.
"""
import copy
from types import SimpleNamespace

import boto3
import pytest
from botocore.exceptions import ClientError
from botocore.stub import Stubber

from providers.base import ModelProvider, ModelRequest, ProviderError, ToolSpec, Usage
from providers.bedrock.converse import BedrockProvider
from providers.bedrock.errors import BedrockError, format_bedrock_client_error
from providers.bedrock import pricing
from providers.reply_text import sanitize_assistant_reply

pytestmark = pytest.mark.requisito("RF-005")

HAIKU = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
SONNET = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
NOVA = "amazon.nova-lite-v1:0"


def make_settings(**over):
    base = dict(
        BEDROCK_REGION="us-east-1",
        BEDROCK_IMAGE_REGION="us-west-2",
        BEDROCK_IMAGE_MODEL_ID="stability.stable-image-core-v1:1",
        BEDROCK_USE_CONVERSE_STREAM=False,
        BEDROCK_PROMPT_CACHE_ENABLED=True,
        AWS_ACCESS_KEY_ID="AKIAFAKEFAKEFAKEFAKE",
        AWS_SECRET_ACCESS_KEY="fake-secret",
    )
    base.update(over)
    return SimpleNamespace(**base)


def fake_boto_client():
    return boto3.client(
        "bedrock-runtime",
        region_name="us-east-1",
        aws_access_key_id="AKIAFAKEFAKEFAKEFAKE",
        aws_secret_access_key="fake-secret",
    )


def provider_with(client, **settings_over):
    return BedrockProvider(make_settings(**settings_over), runtime_client=client)


USER_MSG = {"role": "user", "content": [{"text": "hola"}]}
TOOL = ToolSpec(name="list_x", description="lista x", input_schema={"type": "object", "properties": {}})
TOOL_WIRE = {"toolSpec": {"name": "list_x", "description": "lista x", "inputSchema": {"json": {"type": "object", "properties": {}}}}}
CACHE = {"cachePoint": {"type": "default"}}


def text_response(text="ok", usage=None, stop="end_turn", extra_blocks=()):
    return {
        "output": {"message": {"role": "assistant", "content": [*extra_blocks, {"text": text}]}},
        "stopReason": stop,
        "usage": usage or {"inputTokens": 10, "outputTokens": 5, "totalTokens": 15},
        "metrics": {"latencyMs": 1},
    }


# ---------------------------------------------------------------------------
# Mapeo petición / respuesta (Converse no streaming)
# ---------------------------------------------------------------------------

async def test_provider_satisfies_protocol():
    assert isinstance(provider_with(fake_boto_client()), ModelProvider)


async def test_request_mapping_without_cache_and_response_mapping():
    client = fake_boto_client()
    stub = Stubber(client)
    stub.add_response(
        "converse",
        text_response(
            "respuesta",
            usage={"inputTokens": 7, "outputTokens": 3, "totalTokens": 10},
            extra_blocks=[
                {"reasoningContent": {"reasoningText": {"text": "secreto interno"}}},
                {"toolUse": {"toolUseId": "tu-1", "name": "list_x", "input": {"a": 1}}},
            ],
            stop="tool_use",
        ),
        expected_params={
            "modelId": NOVA,
            "messages": [USER_MSG],
            "system": [{"text": "sys"}],
            "inferenceConfig": {"maxTokens": 512},
            "toolConfig": {"tools": [TOOL_WIRE]},
        },
    )
    with stub:
        resp = await provider_with(client).converse(
            ModelRequest(model_id=NOVA, messages=[USER_MSG], system_prompt="sys", tools=[TOOL], max_tokens=512)
        )
    stub.assert_no_pending_responses()
    assert resp.text == "respuesta"  # reasoningContent nunca llega al texto
    assert resp.stop_reason == "tool_use"
    assert resp.usage == Usage(input_tokens=7, output_tokens=3, cache_read_tokens=0, cache_write_tokens=0)
    assert [(c.id, c.name, c.input) for c in resp.tool_calls] == [("tu-1", "list_x", {"a": 1})]


async def test_tool_use_without_input_defaults_to_empty_dict():
    client = fake_boto_client()
    stub = Stubber(client)
    stub.add_response(
        "converse",
        text_response("", extra_blocks=[{"toolUse": {"toolUseId": "t", "name": "n", "input": {}}}]),
    )
    with stub:
        resp = await provider_with(client).converse(ModelRequest(model_id=NOVA, messages=[USER_MSG], system_prompt="s"))
    assert resp.tool_calls[0].input == {}


async def test_force_tool_use_sets_tool_choice_any_and_no_tools_means_no_tool_config():
    client = fake_boto_client()
    stub = Stubber(client)
    stub.add_response(
        "converse",
        text_response(),
        expected_params={
            "modelId": NOVA, "messages": [USER_MSG], "system": [{"text": "s"}],
            "inferenceConfig": {"maxTokens": 4096},
            "toolConfig": {"tools": [TOOL_WIRE], "toolChoice": {"any": {}}},
        },
    )
    stub.add_response(
        "converse",
        text_response(),
        expected_params={
            "modelId": NOVA, "messages": [USER_MSG], "system": [{"text": "s"}],
            "inferenceConfig": {"maxTokens": 4096},
        },
    )
    prov = provider_with(client)
    with stub:
        await prov.converse(ModelRequest(NOVA, [USER_MSG], "s", [TOOL], force_tool_use=True))
        await prov.converse(ModelRequest(NOVA, [USER_MSG], "s", [], force_tool_use=True))
    stub.assert_no_pending_responses()


async def test_assistant_text_is_sanitized_of_think_markup():
    client = fake_boto_client()
    stub = Stubber(client)
    stub.add_response("converse", text_response("<thinking>plan</thinking>Hola"))
    with stub:
        resp = await provider_with(client).converse(ModelRequest(NOVA, [USER_MSG], "s"))
    assert resp.text == "Hola"


def test_sanitize_assistant_reply_variants():
    assert sanitize_assistant_reply("") == ""
    assert sanitize_assistant_reply("<think>a</think>b") == "b"
    assert sanitize_assistant_reply("a<think>sin cierre") == "a"
    assert sanitize_assistant_reply("<think>solo esto</think>") == "solo esto"


# ---------------------------------------------------------------------------
# cachePoint (ADR-019)
# ---------------------------------------------------------------------------

async def test_cache_points_at_system_tools_and_last_message_without_mutating_input():
    client = fake_boto_client()
    messages = [USER_MSG, {"role": "assistant", "content": [{"text": "a"}]}, {"role": "user", "content": [{"text": "b"}]}]
    original = copy.deepcopy(messages)
    stub = Stubber(client)
    stub.add_response(
        "converse",
        text_response(usage={"inputTokens": 1, "outputTokens": 2, "totalTokens": 9,
                             "cacheReadInputTokens": 4, "cacheWriteInputTokens": 2}),
        expected_params={
            "modelId": HAIKU,
            "messages": [messages[0], messages[1], {"role": "user", "content": [{"text": "b"}, CACHE]}],
            "system": [{"text": "sys"}, CACHE],
            "inferenceConfig": {"maxTokens": 100},
            "toolConfig": {"tools": [TOOL_WIRE, CACHE]},
        },
    )
    with stub:
        resp = await provider_with(client).converse(ModelRequest(HAIKU, messages, "sys", [TOOL], max_tokens=100))
    assert messages == original, "agent_loop sigue extendiendo `messages`: no se puede mutar"
    assert resp.usage.cache_read_tokens == 4 and resp.usage.cache_write_tokens == 2


def test_cache_points_are_fresh_instances():
    from providers.bedrock.converse import build_converse_kwargs

    kwargs = build_converse_kwargs(
        make_settings(), model_id=SONNET, messages=[USER_MSG], system_prompt="s",
        tools=[TOOL], max_tokens=10, force_tool_use=False,
    )
    points = [kwargs["system"][1], kwargs["toolConfig"]["tools"][1], kwargs["messages"][0]["content"][1]]
    assert all(p == CACHE for p in points)
    assert len({id(p) for p in points}) == 3


@pytest.mark.parametrize(
    "model_id, enabled",
    [(NOVA, True), (HAIKU, False), ("modelo.desconocido", True)],
)
def test_no_cache_points_when_unsupported_or_kill_switch_off(model_id, enabled):
    from providers.bedrock.converse import build_converse_kwargs

    kwargs = build_converse_kwargs(
        make_settings(BEDROCK_PROMPT_CACHE_ENABLED=enabled), model_id=model_id, messages=[USER_MSG],
        system_prompt="s", tools=[TOOL], max_tokens=10, force_tool_use=False,
    )
    assert kwargs["system"] == [{"text": "s"}]
    assert kwargs["toolConfig"]["tools"] == [TOOL_WIRE]
    assert kwargs["messages"] == [USER_MSG]


# ---------------------------------------------------------------------------
# Streaming
# ---------------------------------------------------------------------------

class FakeStreamClient:
    """Doble del cliente boto3 para ConverseStream (el Stubber no modela EventStream)."""

    def __init__(self, events=None, stream_error=None, converse_response=None):
        self.events = events or []
        self.stream_error = stream_error
        self.converse_response = converse_response
        self.calls = []

    def converse_stream(self, **kwargs):
        self.calls.append(("converse_stream", kwargs))
        if self.stream_error:
            raise self.stream_error
        return {"stream": iter(self.events)}

    def converse(self, **kwargs):
        self.calls.append(("converse", kwargs))
        return self.converse_response


def client_error(code, message="boom"):
    return ClientError({"Error": {"Code": code, "Message": message}}, "Converse")


STREAM_EVENTS = [
    {"messageStart": {"role": "assistant"}},
    {"contentBlockDelta": {"delta": {"text": "Ho"}, "contentBlockIndex": 0}},
    {"contentBlockDelta": {"delta": {"text": "la"}, "contentBlockIndex": 0}},
    {"contentBlockStart": {"start": {"toolUse": {"toolUseId": "tu-1", "name": "list_x"}}, "contentBlockIndex": 1}},
    {"contentBlockDelta": {"delta": {"toolUse": {"input": '{"a": '}}, "contentBlockIndex": 1}},
    {"contentBlockDelta": {"delta": {"toolUse": {"input": "1}"}}, "contentBlockIndex": 1}},
    {"contentBlockStop": {"contentBlockIndex": 1}},
    {"messageStop": {"stopReason": "tool_use"}},
    {"metadata": {"usage": {"inputTokens": 5, "outputTokens": 6, "cacheReadInputTokens": 2, "cacheWriteInputTokens": None}}},
]


async def test_stream_mode_consumes_stream_into_one_response():
    client = FakeStreamClient(events=STREAM_EVENTS)
    resp = await provider_with(client, BEDROCK_USE_CONVERSE_STREAM=True).converse(
        ModelRequest(NOVA, [USER_MSG], "s", [TOOL])
    )
    assert [c[0] for c in client.calls] == ["converse_stream"]
    assert resp.text == "Hola" and resp.stop_reason == "tool_use"
    assert [(c.id, c.name, c.input, c.input_parse_error) for c in resp.tool_calls] == [("tu-1", "list_x", {"a": 1}, None)]
    assert resp.usage == Usage(input_tokens=5, output_tokens=6, cache_read_tokens=2, cache_write_tokens=0)


async def test_stream_invalid_tool_json_reports_parse_error_with_empty_input():
    events = [
        {"contentBlockStart": {"start": {"toolUse": {"toolUseId": "t", "name": "n"}}, "contentBlockIndex": 0}},
        {"contentBlockDelta": {"delta": {"toolUse": {"input": '{"a": "x'}}, "contentBlockIndex": 0}},
        {"contentBlockStart": {"start": {"toolUse": {"toolUseId": "t2", "name": "m"}}, "contentBlockIndex": 1}},
        {"messageStop": {"stopReason": "max_tokens"}},
    ]
    resp = await provider_with(FakeStreamClient(events=events), BEDROCK_USE_CONVERSE_STREAM=True).converse(
        ModelRequest(NOVA, [USER_MSG], "s")
    )
    bad, empty = resp.tool_calls
    assert bad.input == {} and "Invalid JSON in tool arguments" in bad.input_parse_error
    assert "escape quotes and newlines" in bad.input_parse_error
    assert empty.input == {} and empty.input_parse_error is None
    assert resp.stop_reason == "max_tokens"


async def test_stream_access_denied_falls_back_to_plain_converse():
    client = FakeStreamClient(
        stream_error=client_error("AccessDeniedException", "no InvokeModelWithResponseStream"),
        converse_response=text_response("via converse"),
    )
    resp = await provider_with(client, BEDROCK_USE_CONVERSE_STREAM=True).converse(ModelRequest(NOVA, [USER_MSG], "s"))
    assert [c[0] for c in client.calls] == ["converse_stream", "converse"]
    assert resp.text == "via converse"


async def test_stream_access_denied_then_fallback_failure_raises_bedrock_error():
    class Both(FakeStreamClient):
        def converse(self, **kwargs):
            raise client_error("ThrottlingException", "Too many requests")

    client = Both(stream_error=client_error("AccessDeniedException", "x"))
    with pytest.raises(BedrockError, match=r"Error Bedrock \(ThrottlingException\): Too many requests"):
        await provider_with(client, BEDROCK_USE_CONVERSE_STREAM=True).converse(ModelRequest(NOVA, [USER_MSG], "s"))


async def test_converse_stream_yields_neutral_events_in_order():
    client = FakeStreamClient(events=STREAM_EVENTS)
    events = [e async for e in provider_with(client).converse_stream(ModelRequest(NOVA, [USER_MSG], "s", [TOOL]))]
    kinds = [e.kind for e in events]
    assert kinds == ["text", "text", "tool_call", "stop", "usage"]
    assert "".join(e.text for e in events if e.kind == "text") == "Hola"
    call = next(e.tool_call for e in events if e.kind == "tool_call")
    assert (call.id, call.name, call.input) == ("tu-1", "list_x", {"a": 1})
    assert next(e.stop_reason for e in events if e.kind == "stop") == "tool_use"
    assert next(e.usage for e in events if e.kind == "usage") == Usage(5, 6, 2, 0)


async def test_converse_stream_error_is_wrapped():
    client = FakeStreamClient(stream_error=client_error("ThrottlingException", "slow down"))
    with pytest.raises(BedrockError, match="ThrottlingException"):
        async for _ in provider_with(client).converse_stream(ModelRequest(NOVA, [USER_MSG], "s")):
            pass


# ---------------------------------------------------------------------------
# Errores (throttling y demás)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "code, message, expected",
    [
        ("ThrottlingException", "Too many requests, please wait", "Error Bedrock (ThrottlingException): Too many requests, please wait"),
        ("ServiceQuotaExceededException", "cuota", "Error Bedrock (ServiceQuotaExceededException): cuota"),
        ("AccessDeniedException", "falta bedrock:InvokeModel", "Permisos IAM insuficientes en AWS Bedrock (bedrock:InvokeModel)"),
        ("AccessDeniedException", "InvokeModelWithResponseStream", "(bedrock:InvokeModelWithResponseStream)"),
        ("ValidationException", "conversation must start with a user message", "debe empezar con un mensaje de usuario"),
        ("ValidationException", "otro", f"Error de validación Bedrock ({NOVA}): otro"),
        ("ResourceNotFoundException", "nope", f"Modelo Bedrock no disponible o no habilitado: '{NOVA}'"),
    ],
)
async def test_client_errors_map_to_bedrock_error_with_readable_message(code, message, expected):
    client = fake_boto_client()
    stub = Stubber(client)
    stub.add_client_error("converse", service_error_code=code, service_message=message)
    with stub, pytest.raises(BedrockError) as info:
        await provider_with(client).converse(ModelRequest(NOVA, [USER_MSG], "s"))
    assert expected in str(info.value)
    assert isinstance(info.value, ProviderError)
    assert isinstance(info.value.__cause__, ClientError)


async def test_non_client_error_is_wrapped_with_generic_message():
    class Boom(FakeStreamClient):
        def converse(self, **kwargs):
            raise RuntimeError("socket roto")

    with pytest.raises(BedrockError, match="Converse request failed: socket roto"):
        await provider_with(Boom()).converse(ModelRequest(NOVA, [USER_MSG], "s"))


def test_format_error_for_plain_exception():
    assert format_bedrock_client_error(ValueError("x"), model_id=NOVA) == "Converse request failed: x"


async def test_missing_aws_credentials_raise_before_any_call():
    prov = BedrockProvider(make_settings(AWS_ACCESS_KEY_ID=""))
    with pytest.raises(BedrockError, match="Missing AWS credentials"):
        await prov.converse(ModelRequest(NOVA, [USER_MSG], "s"))


# ---------------------------------------------------------------------------
# Cliente boto3 (client.py): construcción con valores falsos, sin red
# ---------------------------------------------------------------------------

def test_runtime_client_uses_configured_region_and_is_cached():
    from providers.bedrock import client as client_mod

    client_mod.reset_clients()
    s = make_settings(BEDROCK_REGION="eu-west-1")
    first = client_mod.get_runtime_client(s)
    assert first.meta.region_name == "eu-west-1"
    assert client_mod.get_runtime_client(s) is first
    client_mod.reset_clients()


def test_runtime_client_requires_credentials():
    from providers.bedrock import client as client_mod

    client_mod.reset_clients()
    with pytest.raises(BedrockError, match="Missing AWS credentials"):
        client_mod.get_runtime_client(make_settings(AWS_ACCESS_KEY_ID=""))


# ---------------------------------------------------------------------------
# Precios y coste
# ---------------------------------------------------------------------------

def test_cost_uses_price_table_per_million_tokens():
    prov = provider_with(fake_boto_client())
    assert prov.estimate_cost(HAIKU, Usage(input_tokens=1_000_000, output_tokens=1_000_000)) == pytest.approx(6.00)
    assert prov.estimate_cost(NOVA, Usage(input_tokens=1_000_000, output_tokens=1_000_000)) == pytest.approx(0.30)
    assert prov.estimate_cost(SONNET, Usage(input_tokens=2_000_000, output_tokens=1_000_000)) == pytest.approx(21.00)


def test_cost_cache_read_is_0_10x_and_write_is_1_25x_of_input_price():
    prov = provider_with(fake_boto_client())
    assert prov.estimate_cost(HAIKU, Usage(cache_read_tokens=1_000_000)) == pytest.approx(0.10)
    assert prov.estimate_cost(HAIKU, Usage(cache_write_tokens=1_000_000)) == pytest.approx(1.25)
    total = prov.estimate_cost(HAIKU, Usage(1_000_000, 1_000_000, 1_000_000, 1_000_000))
    assert total == pytest.approx(1.0 + 5.0 + 0.10 + 1.25)


def test_cost_of_unknown_model_is_zero_and_savings_formula():
    prov = provider_with(fake_boto_client())
    assert prov.estimate_cost("desconocido", Usage(5, 5, 5, 5)) == 0
    assert pricing.cache_read_savings_usd(HAIKU, 1_000_000) == pytest.approx(0.90)
    assert pricing.cache_read_savings_usd("desconocido", 1_000_000) == 0


def test_list_models_exposes_the_catalog_with_prices_and_cache_flags():
    models = {m.model_id: m for m in provider_with(fake_boto_client()).list_models()}
    assert set(models) == {NOVA, "deepseek.v3.2", HAIKU, "mistral.mistral-large-2402-v1:0", SONNET}
    assert models[HAIKU].price_input_per_million == 1.00 and models[HAIKU].price_output_per_million == 5.00
    assert models[HAIKU].supports_prompt_cache and models[SONNET].supports_prompt_cache
    assert not models[NOVA].supports_prompt_cache
    assert models[SONNET].tier == "premium" and models[HAIKU].invoke_via == "inference_profile"


async def test_wrapped_errors_keep_the_traceback_in_the_log(caplog):
    class Boom(FakeStreamClient):
        def converse(self, **kwargs):
            raise RuntimeError("socket roto")

    with caplog.at_level("ERROR", logger="providers.bedrock.converse"):
        with pytest.raises(BedrockError):
            await provider_with(Boom()).converse(ModelRequest(NOVA, [USER_MSG], "s"))
    records = [r for r in caplog.records if r.levelname == "ERROR"]
    assert records and records[0].exc_info and records[0].exc_info[0] is RuntimeError
