"""
Generación de imágenes — Bedrock Titan Image Generator v2.

Sube bytes a MinIO vía tools.generate_image. Ver ADR-010.
"""
import asyncio
import json
import logging

import boto3

from config import settings
from services.bedrock.errors import BedrockError

logger = logging.getLogger(__name__)

_client = None


def _client():
    global _client
    if _client is None:
        _client = boto3.client(
            "bedrock-runtime",
            region_name=settings.BEDROCK_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
    return _client


async def generate_image_bytes(prompt: str, width: int = 1200, height: int = 627) -> bytes:
    """Invoca Titan Image y devuelve PNG bytes."""

    def _invoke():
        body = json.dumps({
            "taskType": "TEXT_IMAGE",
            "textToImageParams": {"text": prompt},
            "imageGenerationConfig": {"numberOfImages": 1, "width": width, "height": height, "quality": "standard"},
        })
        return _client().invoke_model(
            modelId=settings.BEDROCK_IMAGE_MODEL_ID,
            body=body,
            contentType="application/json",
            accept="application/json",
        )

    try:
        response = await asyncio.to_thread(_invoke)
        payload = json.loads(response["body"].read())
        import base64

        b64 = payload["images"][0]
        return base64.b64decode(b64)
    except Exception as e:
        logger.exception("Image generation failed")
        raise BedrockError(f"Image generation failed: {e}") from e
