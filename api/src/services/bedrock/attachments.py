"""
Adjuntos de chat — valida archivos del usuario y construye content blocks Converse.
"""
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.file_upload import FileUpload
from services import storage_service
from services.bedrock.errors import BedrockError

logger = logging.getLogger(__name__)

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


async def build_user_content_blocks(
    db: AsyncSession,
    user_id: int,
    message: str,
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
        result = await db.execute(
            select(FileUpload).where(FileUpload.id == file_id, FileUpload.user_id == user_id, FileUpload.is_active.is_(True))
        )
        row = result.scalar_one_or_none()
        if row is None:
            raise BedrockError(f"Adjunto no encontrado: file_id={file_id}")
        if row.file_size > _MAX_BYTES:
            raise BedrockError(f"Adjunto demasiado grande (máx {_MAX_BYTES // (1024*1024)} MB): {row.original_filename}")

        response = storage_service.get_object_stream(row.stored_filename)
        try:
            data = response.read()
        finally:
            response.close()
            response.release_conn()

        mime = (row.mime_type or "").lower()
        label = f"[Adjunto: {row.original_filename}]"

        if mime in _IMAGE_MIMES:
            blocks.append({
                "image": {
                    "format": _IMAGE_MIMES[mime],
                    "source": {"bytes": data},
                }
            })
            text_parts.append(f"{label} (imagen incluida)")
        elif mime in _DOC_MIMES:
            blocks.append({
                "document": {
                    "format": _DOC_MIMES[mime],
                    "name": row.original_filename[:100],
                    "source": {"bytes": data},
                }
            })
            text_parts.append(f"{label} (documento incluido)")
        elif mime.startswith("text/") or mime in ("application/json",):
            excerpt = data.decode("utf-8", errors="replace")[:8000]
            text_parts.append(f"{label}\n{excerpt}")
        else:
            url = row.download_url or storage_service.get_presigned_url(row.stored_filename)
            text_parts.append(f"{label} URL: {url}")

    if text_parts:
        blocks.insert(0, {"text": "\n\n".join(text_parts)})
    elif not blocks:
        blocks.append({"text": message or ""})

    return blocks
