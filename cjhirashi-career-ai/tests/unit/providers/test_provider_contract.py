"""Contrato del Protocol ModelProvider y sus tipos neutros (spec 009, RF-005)."""
import inspect
from typing import AsyncIterator, List

import pytest

from providers.base import (
    ImageOptions,
    ImageResult,
    ModelInfo,
    ModelProvider,
    ModelRequest,
    ModelResponse,
    ProviderError,
    StreamEvent,
    ToolCall,
    ToolSpec,
    Usage,
)

pytestmark = pytest.mark.requisito("RF-005")


class FakeProvider:
    """Doble mínimo: cumple el protocolo sin SDK de AWS."""

    async def converse(self, request: ModelRequest) -> ModelResponse:
        return ModelResponse(
            text="hola",
            stop_reason="end_turn",
            usage=Usage(input_tokens=3, output_tokens=2),
            tool_calls=[],
        )

    async def converse_stream(self, request: ModelRequest) -> AsyncIterator[StreamEvent]:
        yield StreamEvent(kind="text", text="ho")
        yield StreamEvent(kind="stop", stop_reason="end_turn")

    async def generate_image(self, prompt: str, options: ImageOptions) -> ImageResult:
        return ImageResult(data=b"png")

    def list_models(self) -> List[ModelInfo]:
        return [ModelInfo(model_id="m", label="M", tier="economy")]

    def estimate_cost(self, model_id: str, usage: Usage) -> float:
        return 0.0


def test_fake_provider_satisfies_protocol():
    assert isinstance(FakeProvider(), ModelProvider)


def test_object_without_surface_is_not_a_provider():
    class Incomplete:
        async def converse(self, request): ...

    assert not isinstance(Incomplete(), ModelProvider)


def test_protocol_surface_is_exactly_the_five_methods():
    names = {n for n in dir(ModelProvider) if not n.startswith("_")}
    assert names == {"converse", "converse_stream", "generate_image", "list_models", "estimate_cost"}


async def test_fake_provider_flow_with_neutral_types():
    provider = FakeProvider()
    req = ModelRequest(
        model_id="m",
        messages=[{"role": "user", "content": [{"text": "hi"}]}],
        system_prompt="sys",
        tools=[ToolSpec(name="t", description="d", input_schema={"type": "object"})],
    )
    assert req.max_tokens == 4096 and req.force_tool_use is False
    resp = await provider.converse(req)
    assert resp.text == "hola" and resp.tool_calls == []
    assert resp.usage.cache_read_tokens == 0 and resp.usage.cache_write_tokens == 0
    events = [e async for e in provider.converse_stream(req)]
    assert [e.kind for e in events] == ["text", "stop"]
    assert (await provider.generate_image("p", ImageOptions())).data == b"png"
    assert ImageOptions().aspect_ratio == "1:1"


def test_tool_call_defaults_and_error_type():
    call = ToolCall(id="u1", name="t", input={"a": 1})
    assert call.input_parse_error is None
    assert issubclass(ProviderError, Exception)


def test_estimate_cost_is_sync_and_converse_is_coroutine():
    assert inspect.iscoroutinefunction(FakeProvider.converse)
    assert not inspect.iscoroutinefunction(FakeProvider.estimate_cost)
