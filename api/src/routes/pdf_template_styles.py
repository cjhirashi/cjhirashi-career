"""
CRUD de estilos CSS reutilizables para plantillas PDF.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from middleware.auth import get_current_user
from models.pdf_template_style import PdfTemplateStyle
from models.user import User
from repositories.career_repository import CareerRepository
from schemas.pdf_template import (
    PdfTemplateStyleCreate,
    PdfTemplateStyleResponse,
    PdfTemplateStyleUpdate,
)
from services.id_generator import normalize_prefixed_id

router = APIRouter(prefix="/pdf-template-styles", tags=["PDF Template Styles"])

_repo = CareerRepository(PdfTemplateStyle, resource_key="pdf-template-styles", vectorize=False)


@router.get("", response_model=list[PdfTemplateStyleResponse])
async def list_styles(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _repo.list_for_user(db, current_user.id, skip=skip, limit=limit)


@router.get("/{style_id}", response_model=PdfTemplateStyleResponse)
async def get_style(
    style_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    style_id = normalize_prefixed_id("pdf_template_styles", style_id)
    row = await _repo.get_for_user(db, current_user.id, style_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Style not found")
    return row


@router.post("", response_model=PdfTemplateStyleResponse, status_code=status.HTTP_201_CREATED)
async def create_style(
    payload: PdfTemplateStyleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _repo.create_for_user(db, current_user.id, payload.model_dump())


@router.put("/{style_id}", response_model=PdfTemplateStyleResponse)
async def update_style(
    style_id: str,
    payload: PdfTemplateStyleUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    style_id = normalize_prefixed_id("pdf_template_styles", style_id)
    row = await _repo.get_for_user(db, current_user.id, style_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Style not found")
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        if hasattr(row, key):
            setattr(row, key, value)
    await db.commit()
    await db.refresh(row)
    return row


@router.delete("/{style_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_style(
    style_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    style_id = normalize_prefixed_id("pdf_template_styles", style_id)
    deleted = await _repo.delete_for_user(db, current_user.id, style_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Style not found")
