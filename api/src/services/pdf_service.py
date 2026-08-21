"""
PDF Generator client - renders a title + Markdown body into a PDF via the
`pdf_generator` container (internal-only, same `network-cjhirashi-srv`).
Mirrors github_service.py's thin-httpx-wrapper shape.
"""
import logging

import httpx

from config import settings

logger = logging.getLogger(__name__)

# Rendering a full document (Markdown -> HTML -> PDF) can take a while under
# load - generous on purpose, this is a synchronous user-triggered download,
# not a hot path.
_TIMEOUT_SECONDS = 30.0


class PDFGeneratorError(Exception):
    pass


async def generate_markdown_document(title: str, content: str) -> bytes:
    """POSTs to pdf_generator's `/generate/markdown-document` and returns the
    raw PDF bytes."""
    url = f"{settings.PDF_GENERATOR_URL}/generate/markdown-document"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
            response = await client.post(url, json={"title": title, "content": content})
    except httpx.RequestError as e:
        logger.error(f"PDF Generator unreachable at {url}: {e}")
        raise PDFGeneratorError("El servicio de generación de PDF no está disponible") from e

    if response.status_code != 200:
        logger.error(f"PDF Generator returned {response.status_code}: {response.text}")
        raise PDFGeneratorError(f"El servicio de generación de PDF respondió con un error ({response.status_code})")

    return response.content
