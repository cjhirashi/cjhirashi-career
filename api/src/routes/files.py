"""
File upload routes - MinIO-backed bucket with public download links.

Every write (upload/delete) requires JWT auth and is scoped to the
authenticated user, same row-level-isolation pattern as
`routes/career_common.py`. Reads of an already-uploaded object's public URL
need no auth by design - that's the whole point of "generar links públicos".
"""
import io
from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from middleware.auth import get_current_user
from models.file_upload import FileUpload, FileType
from models.user import User
from schemas.file_upload import FileUploadResponse
from services import storage_service
from config import settings

router = APIRouter(prefix="/files", tags=["Files"])


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


@router.post("", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    description: str = Form(None),
    category: str = Form(None),
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
    stored_filename = storage_service.upload_file(
        data=io.BytesIO(contents),
        original_filename=file.filename,
        size=len(contents),
        content_type=content_type,
        category=category,
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
        is_public=True,
        download_url=storage_service.get_public_url(stored_filename),
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


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: int,
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
