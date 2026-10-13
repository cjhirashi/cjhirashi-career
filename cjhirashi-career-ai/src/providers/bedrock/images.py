"""
Generación de imágenes — Bedrock Stability Stable Image Core (ADR-010, ADR-025).

Traslado de `cjhirashi-career-api/src/services/bedrock/image_client.py`. Titan Image Generator
llegó a fin de vida y Nova Canvas no tiene acceso habilitado; Stable Image Core solo está en
us-west-2, de ahí `BEDROCK_IMAGE_REGION` separado de `BEDROCK_REGION`. Devuelve los bytes PNG;
el recorte, el almacenamiento y el registro de uso son del servicio de imágenes.
"""
import asyncio
import base64
import json
import logging
from typing import Any

from providers.base import ImageOptions
from providers.bedrock.errors import BedrockError

logger = logging.getLogger(__name__)

# Valores fijos que acepta el modelo; el recorte a la medida exacta del propósito lo hace
# después el pipeline de imágenes.
SUPPORTED_ASPECT_RATIOS = frozenset({"1:1", "16:9", "21:9", "2:3", "3:2", "4:5", "5:4", "9:16", "9:21"})


def validate_params(prompt: str, options: ImageOptions) -> None:
    if not (prompt or "").strip():
        raise BedrockError("prompt vacío: describe qué imagen generar")
    if options.aspect_ratio not in SUPPORTED_ASPECT_RATIOS:
        raise BedrockError(
            f"aspect_ratio no soportado: '{options.aspect_ratio}' "
            f"(válidos: {', '.join(sorted(SUPPORTED_ASPECT_RATIOS))})"
        )


async def generate_image_bytes(client: Any, settings: Any, prompt: str, options: ImageOptions) -> bytes:
    """Invoca Stable Image Core y devuelve PNG bytes."""
    validate_params(prompt, options)

    def _invoke():
        body = json.dumps({
            "prompt": prompt,
            "aspect_ratio": options.aspect_ratio,
            "output_format": "png",
        })
        return client.invoke_model(
            modelId=settings.BEDROCK_IMAGE_MODEL_ID,
            body=body,
            contentType="application/json",
            accept="application/json",
        )

    try:
        response = await asyncio.to_thread(_invoke)
        payload = json.loads(response["body"].read())
        return base64.b64decode(payload["images"][0])
    except Exception as e:
        logger.exception("Image generation failed")
        raise BedrockError(
            f"Image generation failed (model={settings.BEDROCK_IMAGE_MODEL_ID}, "
            f"region={settings.BEDROCK_IMAGE_REGION}): {e}"
        ) from e
