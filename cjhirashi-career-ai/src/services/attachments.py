"""Adjuntos de chat (RF-005): lee los archivos del usuario por REST y construye content blocks Converse.

Traslado de `cjhirashi-career-api/src/services/bedrock/attachments.py`. `db` y `user_id` se conservan por
compatibilidad de firma y no se usan: el dueño lo fija la credencial en contexto (D-10), no un filtro local.
"""
from typing import Any, Dict, List, Optional

from clients.api_client import ApiError, get_api_client
from clients.career import _ID_RE, _check
from clients.files import FilesClient
from providers.base import ProviderError

_MAX_BYTES = 5 * 1024 * 1024
_IMAGE_MIMES = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/gif": "gif",
    "image/webp": "webp",
}
_DOC_MIMES = {
    "application/pdf": "pdf",
    "text/plain": "txt",
    "text/markdown": "md",
}


async def _metadata(files: FilesClient, file_id: str) -> Dict[str, Any]:
    try:
        _check(file_id, _ID_RE, "id")  # id con caracteres inseguros: nunca se envía petición
    except ValueError:
        raise ProviderError(f"Adjunto no encontrado: file_id={file_id}") from None
    try:
        return await files.get(file_id)
    except ApiError as exc:
        if exc.status == 404:
            raise ProviderError(f"Adjunto no encontrado: file_id={file_id}") from None
        raise


async def build_user_content_blocks(
    db: Any,
    user_id: str,
    message: Optional[str],
    attachments: Optional[List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    """Texto + bloques imagen/documento para Converse API."""
    blocks: List[Dict[str, Any]] = []
    text_parts: List[str] = []

    if message and message.strip():
        text_parts.append(message.strip())

    for raw in attachments or []:
        file_id = raw.get("file_id")
        if not file_id:
            continue
        files = FilesClient(get_api_client())
        row = await _metadata(files, file_id)
        if row["file_size"] > _MAX_BYTES:
            raise ProviderError(
                f"Adjunto demasiado grande (máx {_MAX_BYTES // (1024 * 1024)} MB): {row['original_filename']}"
            )

        data, _ = await files.get_raw(file_id)

        mime = (row.get("mime_type") or "").lower()
        name = row["original_filename"]
        label = f"[Adjunto: {name}]"

        if mime in _IMAGE_MIMES:
            blocks.append({"image": {"format": _IMAGE_MIMES[mime], "source": {"bytes": data}}})
            text_parts.append(f"{label} (imagen incluida)")
        elif mime in _DOC_MIMES:
            blocks.append({"document": {"format": _DOC_MIMES[mime], "name": name[:100], "source": {"bytes": data}}})
            text_parts.append(f"{label} (documento incluido)")
        elif mime.startswith("text/") or mime in ("application/json",):
            excerpt = data.decode("utf-8", errors="replace")[:8000]
            text_parts.append(f"{label}\n{excerpt}")
        else:
            url = row.get("download_url") or await files.get_download_url(file_id)
            text_parts.append(f"{label} URL: {url}")

    if text_parts:
        blocks.insert(0, {"text": "\n\n".join(text_parts)})
    elif not blocks:
        blocks.append({"text": message or ""})

    return blocks
