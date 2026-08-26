"""
Embeddings Titan para búsqueda semántica (Qdrant).

Usa bedrock-runtime (no Converse). Ver docs/BEDROCK-SYSTEM.md.
"""
import asyncio
import json
import logging
from typing import List

import boto3

from config import settings
from services.bedrock.errors import BedrockError

logger = logging.getLogger(__name__)

_embedding_client = None


# ============================================================================
# Cliente de embeddings
# ============================================================================

def _require_aws() -> None:
    if not settings.AWS_ACCESS_KEY_ID or not settings.AWS_SECRET_ACCESS_KEY:
        raise BedrockError("Bedrock is not configured (missing AWS credentials)")


def _get_embedding_client():
    global _embedding_client
    if _embedding_client is None:
        _require_aws()
        _embedding_client = boto3.client(
            "bedrock-runtime",
            region_name=settings.BEDROCK_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
    return _embedding_client


# ============================================================================
# Vectorización de texto
# ============================================================================

async def embed_text(text: str) -> List[float]:
    """Vectoriza texto con Titan Embeddings v2."""
    client = _get_embedding_client()

    def _invoke():
        return client.invoke_model(
            modelId=settings.BEDROCK_EMBEDDING_MODEL_ID,
            body=json.dumps({"inputText": text}),
            contentType="application/json",
            accept="application/json",
        )

    try:
        response = await asyncio.to_thread(_invoke)
        payload = json.loads(response["body"].read())
        return payload["embedding"]
    except Exception as e:
        logger.exception("Titan embedding failed")
        raise BedrockError(f"Embedding failed: {e}") from e
