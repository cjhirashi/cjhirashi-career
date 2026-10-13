"""RF-005: generación de imágenes con Stability vía Bedrock (ADR-025) y fábrica de proveedor (T-025).

Sin red ni AWS: `Stubber` sobre un cliente boto3 real con credenciales falsas.
"""
import base64
import json
from io import BytesIO
from types import SimpleNamespace

import boto3
import pytest
from botocore.response import StreamingBody
from botocore.stub import Stubber

from providers.base import ImageOptions, ImageResult, ModelProvider, ProviderError
from providers.bedrock.converse import BedrockProvider
from providers.bedrock.errors import BedrockError

pytestmark = pytest.mark.requisito("RF-005")

IMAGE_MODEL = "stability.stable-image-core-v1:1"
PNG = b"\x89PNG\r\n\x1a\nfake-bytes"


def make_settings(**over):
    base = dict(
        BEDROCK_REGION="us-east-1",
        BEDROCK_IMAGE_REGION="us-west-2",
        BEDROCK_IMAGE_MODEL_ID=IMAGE_MODEL,
        BEDROCK_USE_CONVERSE_STREAM=False,
        BEDROCK_PROMPT_CACHE_ENABLED=True,
        AWS_ACCESS_KEY_ID="AKIAFAKEFAKEFAKEFAKE",
        AWS_SECRET_ACCESS_KEY="fake-secret",
    )
    base.update(over)
    return SimpleNamespace(**base)


def fake_image_client():
    return boto3.client(
        "bedrock-runtime", region_name="us-west-2",
        aws_access_key_id="AKIAFAKEFAKEFAKEFAKE", aws_secret_access_key="fake-secret",
    )


def body_of(payload: dict) -> StreamingBody:
    raw = json.dumps(payload).encode()
    return StreamingBody(BytesIO(raw), len(raw))


def provider_with(client, **over):
    return BedrockProvider(make_settings(**over), image_client=client)


async def test_generate_image_invokes_stability_and_decodes_png():
    client = fake_image_client()
    stub = Stubber(client)
    stub.add_response(
        "invoke_model",
        {"body": body_of({"images": [base64.b64encode(PNG).decode()]}), "contentType": "application/json"},
        expected_params={
            "modelId": IMAGE_MODEL,
            "body": json.dumps({"prompt": "un gato", "aspect_ratio": "16:9", "output_format": "png"}),
            "contentType": "application/json",
            "accept": "application/json",
        },
    )
    with stub:
        result = await provider_with(client).generate_image("un gato", ImageOptions(aspect_ratio="16:9"))
    stub.assert_no_pending_responses()
    assert isinstance(result, ImageResult) and result.data == PNG


async def test_default_aspect_ratio_is_square():
    client = fake_image_client()
    stub = Stubber(client)
    stub.add_response(
        "invoke_model",
        {"body": body_of({"images": [base64.b64encode(PNG).decode()]}), "contentType": "application/json"},
        expected_params={
            "modelId": IMAGE_MODEL,
            "body": json.dumps({"prompt": "x", "aspect_ratio": "1:1", "output_format": "png"}),
            "contentType": "application/json", "accept": "application/json",
        },
    )
    with stub:
        assert (await provider_with(client).generate_image("x", ImageOptions())).data == PNG


async def test_model_id_comes_from_settings():
    client = fake_image_client()
    stub = Stubber(client)
    stub.add_response(
        "invoke_model",
        {"body": body_of({"images": [base64.b64encode(PNG).decode()]}), "contentType": "application/json"},
        expected_params={
            "modelId": "stability.sd3-5-large-v1:0",
            "body": json.dumps({"prompt": "x", "aspect_ratio": "1:1", "output_format": "png"}),
            "contentType": "application/json", "accept": "application/json",
        },
    )
    with stub:
        await provider_with(client, BEDROCK_IMAGE_MODEL_ID="stability.sd3-5-large-v1:0").generate_image("x", ImageOptions())
    stub.assert_no_pending_responses()


@pytest.mark.parametrize("ratio", ["1:1", "16:9", "21:9", "2:3", "3:2", "4:5", "5:4", "9:16", "9:21"])
async def test_every_ratio_accepted_by_the_model_is_valid(ratio):
    client = fake_image_client()
    stub = Stubber(client)
    stub.add_response("invoke_model", {"body": body_of({"images": [base64.b64encode(PNG).decode()]}), "contentType": "application/json"})
    with stub:
        assert (await provider_with(client).generate_image("x", ImageOptions(aspect_ratio=ratio))).data == PNG


# ---------------------------------------------------------------------------
# Validación de parámetros: antes de cualquier llamada
# ---------------------------------------------------------------------------

class ExplodingClient:
    def invoke_model(self, **kwargs):  # pragma: no cover - no debe llamarse
        raise AssertionError("no debe llamar a Bedrock con parámetros inválidos")


@pytest.mark.parametrize("prompt", ["", "   ", "\n"])
async def test_empty_prompt_is_rejected_before_calling_bedrock(prompt):
    with pytest.raises(BedrockError, match="prompt vacío"):
        await provider_with(ExplodingClient()).generate_image(prompt, ImageOptions())


@pytest.mark.parametrize("ratio", ["", "2:1", "square", "1x1"])
async def test_unsupported_aspect_ratio_is_rejected_before_calling_bedrock(ratio):
    with pytest.raises(BedrockError, match="aspect_ratio"):
        await provider_with(ExplodingClient()).generate_image("x", ImageOptions(aspect_ratio=ratio))


# ---------------------------------------------------------------------------
# Errores
# ---------------------------------------------------------------------------

async def test_client_error_is_wrapped_with_model_and_region():
    client = fake_image_client()
    stub = Stubber(client)
    stub.add_client_error("invoke_model", service_error_code="ThrottlingException", service_message="slow down")
    with stub, pytest.raises(BedrockError) as info:
        await provider_with(client).generate_image("x", ImageOptions())
    msg = str(info.value)
    assert f"Image generation failed (model={IMAGE_MODEL}, region=us-west-2)" in msg
    assert "ThrottlingException" in msg
    assert isinstance(info.value, ProviderError) and info.value.__cause__ is not None


async def test_response_without_images_is_wrapped():
    client = fake_image_client()
    stub = Stubber(client)
    stub.add_response("invoke_model", {"body": body_of({"error": "filtered"}), "contentType": "application/json"})
    with stub, pytest.raises(BedrockError, match="Image generation failed"):
        await provider_with(client).generate_image("x", ImageOptions())


async def test_image_client_is_built_in_the_image_region_with_fake_credentials():
    from providers.bedrock import client as client_mod

    client_mod.reset_clients()
    c = client_mod.get_image_client(make_settings())
    assert c.meta.region_name == "us-west-2"
    assert client_mod.get_image_client(make_settings()) is c
    client_mod.reset_clients()


# ---------------------------------------------------------------------------
# Fábrica get_provider() en config
# ---------------------------------------------------------------------------

def test_get_provider_returns_the_bedrock_implementation():
    import config

    provider = config.get_provider()
    assert isinstance(provider, BedrockProvider)
    assert isinstance(provider, ModelProvider)
    assert config.get_provider() is provider  # una instancia por proceso


def test_settings_expose_bedrock_defaults_equal_to_the_api():
    import config

    s = config.settings
    assert s.BEDROCK_REGION == "us-east-1"
    assert s.BEDROCK_IMAGE_REGION == "us-west-2"
    assert s.BEDROCK_IMAGE_MODEL_ID == IMAGE_MODEL
    assert s.BEDROCK_USE_CONVERSE_STREAM is False
    assert s.BEDROCK_PROMPT_CACHE_ENABLED is True
    assert s.AWS_ACCESS_KEY_ID == "" and s.AWS_SECRET_ACCESS_KEY == ""
