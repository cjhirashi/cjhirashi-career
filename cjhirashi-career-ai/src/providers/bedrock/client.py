"""
Clientes boto3 de Bedrock Runtime (traslado de converse_client._get_runtime_client e
image_client._get_client). Único punto donde se construye un cliente AWS (RF-005).

Las imágenes usan una región distinta (Stable Image Core solo está en us-west-2; ADR-010).
Las credenciales y la región vienen de la configuración: aquí no se leen variables de entorno.
"""
from typing import Any, Dict

import boto3

from providers.bedrock.errors import BedrockError

_clients: Dict[str, Any] = {}


def _build(settings: Any, region: str) -> Any:
    return boto3.client(
        "bedrock-runtime",
        region_name=region,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )


def get_runtime_client(settings: Any) -> Any:
    """Cliente de Converse (BEDROCK_REGION), cacheado."""
    if "runtime" not in _clients:
        if not settings.AWS_ACCESS_KEY_ID:
            raise BedrockError("Missing AWS credentials")
        _clients["runtime"] = _build(settings, settings.BEDROCK_REGION)
    return _clients["runtime"]


def get_image_client(settings: Any) -> Any:
    """Cliente de generación de imágenes (BEDROCK_IMAGE_REGION), cacheado."""
    if "image" not in _clients:
        _clients["image"] = _build(settings, settings.BEDROCK_IMAGE_REGION)
    return _clients["image"]


def reset_clients() -> None:
    """Descarta los clientes cacheados (tests)."""
    _clients.clear()
