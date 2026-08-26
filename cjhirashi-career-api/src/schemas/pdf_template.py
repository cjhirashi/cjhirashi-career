"""Schemas — plantillas HTML y estilos CSS para PDF (WeasyPrint)."""
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


# ============================================================================
# Estilos CSS reutilizables
# ============================================================================

class PdfTemplateStyleCreate(BaseModel):
    slug: str = Field(..., min_length=1, max_length=120)
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    css_content: str = Field(..., min_length=1)
    style_guide: Optional[str] = None
    is_active: bool = True


class PdfTemplateStyleUpdate(BaseModel):
    slug: Optional[str] = Field(None, min_length=1, max_length=120)
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    css_content: Optional[str] = Field(None, min_length=1)
    style_guide: Optional[str] = None
    is_active: Optional[bool] = None


class PdfTemplateStyleResponse(BaseModel):
    id: str
    user_id: str
    slug: str
    title: str
    description: Optional[str] = None
    css_content: str
    style_guide: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Plantillas — creación, actualización y respuesta
# ============================================================================

class PdfOutputTemplateCreate(BaseModel):
    slug: str = Field(..., min_length=1, max_length=120)
    document_type: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    html_template: str = Field(..., min_length=1)
    style_id: Optional[str] = None
    variables: Optional[str] = None
    variables_schema: Optional[Dict[str, Any]] = None
    preview_notes: Optional[str] = None
    is_active: bool = True
    is_default: bool = False


class PdfOutputTemplateUpdate(BaseModel):
    slug: Optional[str] = Field(None, min_length=1, max_length=120)
    document_type: Optional[str] = Field(None, min_length=1, max_length=50)
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    html_template: Optional[str] = None
    style_id: Optional[str] = None
    variables: Optional[str] = None
    variables_schema: Optional[Dict[str, Any]] = None
    preview_notes: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class PdfOutputTemplateResponse(BaseModel):
    id: str
    user_id: str
    slug: str
    document_type: str
    title: str
    description: Optional[str] = None
    html_template: str
    style_id: Optional[str] = None
    variables: Optional[str] = None
    variables_schema: Optional[Dict[str, Any]] = None
    preview_notes: Optional[str] = None
    is_active: bool
    is_default: bool
    version: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Renderizado — solicitudes
# ============================================================================

class PdfTemplateRenderRequest(BaseModel):
    variables: Dict[str, Any] = Field(default_factory=dict)
    title: Optional[str] = None
