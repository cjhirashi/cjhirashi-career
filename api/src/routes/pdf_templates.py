"""
CRUD de plantillas PDF + render preview (Harness local / agente pdf_design).
"""
import re

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from middleware.auth import get_current_user
from models.pdf_output_template import PdfOutputTemplate
from models.user import User
from repositories.career_repository import CareerRepository
from schemas.pdf_template import (
    PdfOutputTemplateCreate,
    PdfOutputTemplateResponse,
    PdfOutputTemplateUpdate,
    PdfTemplateRenderRequest,
)
from services.pdf_service import PDFGeneratorError, generate_html_template_pdf
from services.pdf_template_render import render_template_html

router = APIRouter(prefix="/pdf-templates", tags=["PDF Templates"])

_repo = CareerRepository(PdfOutputTemplate, resource_key="pdf-output-templates", vectorize=False)


@router.get("", response_model=list[PdfOutputTemplateResponse])
async def list_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    document_type: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items = await _repo.list_for_user(db, current_user.id, skip=skip, limit=limit)
    if document_type:
        items = [i for i in items if i.document_type == document_type]
    return items


@router.get("/defaults/by-type", response_model=PdfOutputTemplateResponse)
async def get_default_template(
    document_type: str = Query(..., min_length=1),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PdfOutputTemplate).where(
            PdfOutputTemplate.user_id == current_user.id,
            PdfOutputTemplate.document_type == document_type,
            PdfOutputTemplate.is_default.is_(True),
            PdfOutputTemplate.is_active.is_(True),
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No default template for this type")
    return row


@router.get("/{template_id}", response_model=PdfOutputTemplateResponse)
async def get_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    row = await _repo.get_for_user(db, current_user.id, template_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    return row


@router.post("", response_model=PdfOutputTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    payload: PdfOutputTemplateCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _repo.create_for_user(db, current_user.id, payload.model_dump())


@router.put("/{template_id}", response_model=PdfOutputTemplateResponse)
async def update_template(
    template_id: int,
    payload: PdfOutputTemplateUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    row = await _repo.get_for_user(db, current_user.id, template_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        if hasattr(row, k):
            setattr(row, k, v)
    row.version = (row.version or 1) + 1
    await db.commit()
    await db.refresh(row)
    return row


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deleted = await _repo.delete_for_user(db, current_user.id, template_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")


@router.post("/{template_id}/render", summary="Render PDF from stored HTML template")
async def render_pdf_template(
    template_id: int,
    payload: PdfTemplateRenderRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    row = await _repo.get_for_user(db, current_user.id, template_id)
    if row is None or not row.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

    html = render_template_html(row.html_template, payload.variables or {})
    title = payload.title or row.title
    try:
        pdf_bytes = await generate_html_template_pdf(title=title, html_body=html, css_content=row.css_content)
    except PDFGeneratorError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    safe = re.sub(r"[^a-zA-Z0-9]+", "-", title.strip()).strip("-") or "document"
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{safe}.pdf"'},
    )
