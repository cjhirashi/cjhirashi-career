"""
File upload routes - MinIO-backed bucket with public download links.

Every write (upload/delete/visibility change) requires JWT auth and is
scoped to the authenticated user, same row-level-isolation pattern as
`routes/career_common.py`. Reading a *public* file needs no auth by design -
that's the whole point of "generar links públicos" - but reading a *private*
one always goes through this API (get_presigned_url), never a bare bucket
URL: the bucket policy only grants anonymous access under `public/`.
"""
# ============================================================================
# Imports
# ============================================================================
import io
import logging
import re
from typing import List, Tuple

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from PIL import Image, ImageOps, UnidentifiedImageError
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.background import BackgroundTask

from database import get_db
from middleware.auth import get_current_user
from models.file_upload import FileUpload, FileType
from models.user import User
from schemas.file_upload import FileUploadResponse
from services import storage_service
from config import settings

logger = logging.getLogger(__name__)

# ============================================================================
# Router principal
# ============================================================================
router = APIRouter(prefix="/files", tags=["Files"])

# ============================================================================
# Constantes de optimización de imágenes
# ============================================================================
# Uploaded photos routinely come straight off a phone/camera (several MB,
# far larger than anything the portal/admin ever displays) with no
# optimization step anywhere in the pipeline - re-encode on upload instead
# of serving whatever was dropped in, byte for byte.
MAX_IMAGE_DIMENSION = 1920
JPEG_QUALITY = 85


# ============================================================================
# Helpers: optimización y clasificación de imágenes
# ============================================================================
def _has_real_transparency(image: Image.Image) -> bool:
    """True only if the image actually uses transparency (some pixel with
    alpha < 255) - not merely if its color mode has an alpha channel. Photos
    exported from phones/editors routinely carry an RGBA mode with a fully
    opaque alpha channel that's never used, which would otherwise wrongly
    keep them as bloated PNG instead of converting to JPEG."""
    if image.mode not in ("RGBA", "LA") and not (image.mode == "P" and "transparency" in image.info):
        return False
    alpha = image.convert("RGBA").split()[-1]
    return alpha.getextrema()[0] < 255


def _optimize_image(contents: bytes, filename: str) -> Tuple[bytes, str, str]:
    """Resize (long edge capped at MAX_IMAGE_DIMENSION) and re-encode an
    uploaded image. Photos (no alpha channel) become JPEG - far smaller than
    PNG for photographic content at visually equivalent quality. Images with
    real transparency (logos, icons) stay PNG, just resized/optimized.
    Returns (new_bytes, new_content_type, new_filename). Raises on anything
    Pillow can't decode (e.g. SVG) - the caller falls back to the original
    bytes in that case."""
    image = Image.open(io.BytesIO(contents))
    image = ImageOps.exif_transpose(image)  # honor camera rotation before resizing

    if max(image.size) > MAX_IMAGE_DIMENSION:
        image.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION), Image.LANCZOS)

    has_alpha = _has_real_transparency(image)
    base_name = re.sub(r"\.\w+$", "", filename) or "image"
    buffer = io.BytesIO()

    if has_alpha:
        image.convert("RGBA").save(buffer, format="PNG", optimize=True)
        return buffer.getvalue(), "image/png", f"{base_name}.png"

    image.convert("RGB").save(buffer, format="JPEG", quality=JPEG_QUALITY, optimize=True)
    return buffer.getvalue(), "image/jpeg", f"{base_name}.jpg"


def _infer_file_type(content_type: str) -> FileType:
    if content_type.startswith("image/"):
        return FileType.IMAGE
    if content_type in (
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ):
        return FileType.DOCUMENT
    if content_type in ("application/zip", "application/x-rar-compressed", "application/x-tar"):
        return FileType.ARCHIVE
    return FileType.OTHER


# ============================================================================
# Endpoints: subida y listado de archivos
# ============================================================================
@router.post("", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    description: str = Form(None),
    category: str = Form(None),
    is_public: bool = Form(True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    contents = await file.read()
    if len(contents) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"El archivo supera el límite de {settings.MAX_UPLOAD_SIZE // (1024 * 1024)} MB",
        )

    content_type = file.content_type or "application/octet-stream"
    stored_filename_for_key = file.filename

    if content_type.startswith("image/"):
        try:
            contents, content_type, stored_filename_for_key = _optimize_image(contents, file.filename)
        except (UnidentifiedImageError, OSError) as exc:
            # Pillow can't decode some things sent as "image/*" (SVG is the
            # common case) - store the original bytes rather than fail the
            # upload over a format we're not able to optimize.
            logger.warning("Could not optimize '%s' as an image (%s), storing it unmodified", file.filename, exc)

    stored_filename = storage_service.upload_file(
        data=io.BytesIO(contents),
        original_filename=stored_filename_for_key,
        size=len(contents),
        content_type=content_type,
        category=category,
        is_public=is_public,
    )
    # The bucket key's folder is the slugified category (e.g. "Certificaciones"
    # -> "certificaciones/") - store that same slug as the row's category so
    # listing/filtering and the bucket's real folder structure never drift apart.
    category_slug = storage_service.slugify_category(category) if category else None

    row = FileUpload(
        user_id=current_user.id,
        original_filename=file.filename,
        stored_filename=stored_filename,
        file_path=stored_filename,
        file_type=_infer_file_type(content_type),
        mime_type=content_type,
        file_size=len(contents),
        description=description,
        category=category_slug,
        is_public=is_public,
        download_url=storage_service.get_public_url(stored_filename) if is_public else None,
    )
    db.add(row)
    await db.flush()
    await db.refresh(row)
    await db.commit()
    return row


@router.get("", response_model=List[FileUploadResponse])
async def list_files(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category: str = Query(None, description="Filter by folder/category slug"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conditions = [FileUpload.user_id == current_user.id, FileUpload.is_active == True]  # noqa: E712
    if category is not None:
        conditions.append(FileUpload.category == category)
    stmt = (
        select(FileUpload)
        .where(*conditions)
        .order_by(FileUpload.id.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/categories", response_model=List[str])
async def list_categories(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Distinct folder/category slugs the user has uploaded to, for populating
    the "carpeta" picker with what already exists instead of just free text."""
    stmt = (
        select(FileUpload.category)
        .where(
            FileUpload.user_id == current_user.id,
            FileUpload.is_active == True,  # noqa: E712
            FileUpload.category.is_not(None),
        )
        .distinct()
        .order_by(FileUpload.category)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


# ============================================================================
# Schemas auxiliares (visibilidad y URLs firmadas)
# ============================================================================
class VisibilityUpdate(BaseModel):
    is_public: bool


class PresignedUrlResponse(BaseModel):
    url: str


# ============================================================================
# Endpoints: gestión de visibilidad y descarga
# ============================================================================
@router.patch("/{file_id}/visibility", response_model=FileUploadResponse)
async def update_visibility(
    file_id: str,
    payload: VisibilityUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(FileUpload).where(FileUpload.id == file_id, FileUpload.user_id == current_user.id)
    result = await db.execute(stmt)
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Archivo no encontrado")

    if row.is_public != payload.is_public:
        new_key = storage_service.set_visibility(row.stored_filename, row.category, payload.is_public)
        row.stored_filename = new_key
        row.file_path = new_key
        row.is_public = payload.is_public
        row.download_url = storage_service.get_public_url(new_key) if payload.is_public else None
        await db.flush()
        await db.refresh(row)
        await db.commit()
    return row


@router.get("/{file_id}/download", response_model=PresignedUrlResponse)
async def get_download_url(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Short-lived signed URL for *any* owned file, public or private - the
    only way to read a private one (its bare bucket URL is never valid), and
    a convenient escape hatch for a public one too (e.g. previewing before
    the row's own permanent `download_url` is trusted)."""
    stmt = select(FileUpload).where(FileUpload.id == file_id, FileUpload.user_id == current_user.id)
    result = await db.execute(stmt)
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Archivo no encontrado")

    return PresignedUrlResponse(url=storage_service.get_presigned_url(row.stored_filename))


@router.get("/{file_id}/raw")
async def download_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Streams the file's raw bytes through the API (authenticated via the
    normal JWT header, unlike the bucket URLs) so the frontend can force a
    real "Save As" download via a Blob - a plain <a href> to a public/signed
    bucket URL just navigates the browser to it (or is blocked by CORS for a
    fetch() from a different origin), it doesn't reliably download."""
    stmt = select(FileUpload).where(FileUpload.id == file_id, FileUpload.user_id == current_user.id)
    result = await db.execute(stmt)
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Archivo no encontrado")

    obj = storage_service.get_object_stream(row.stored_filename)
    return StreamingResponse(
        obj.stream(32 * 1024),
        media_type=row.mime_type or "application/octet-stream",
        background=BackgroundTask(lambda: (obj.close(), obj.release_conn())),
    )


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(FileUpload).where(FileUpload.id == file_id, FileUpload.user_id == current_user.id)
    result = await db.execute(stmt)
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Archivo no encontrado")

    storage_service.delete_file(row.stored_filename)
    await db.delete(row)
    await db.commit()
