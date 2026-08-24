"""Schemas — plantillas HTML/CSS para PDF (WeasyPrint)."""
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class PdfOutputTemplateCreate(BaseModel):
    slug: str = Field(..., min_length=1, max_length=120)
    document_type: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    html_template: str = Field(..., min_length=1)
    css_content: Optional[str] = None
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
    css_content: Optional[str] = None
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
    css_content: Optional[str] = None
    variables_schema: Optional[Dict[str, Any]] = None
    preview_notes: Optional[str] = None
    is_active: bool
    is_default: bool
    version: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PdfTemplateRenderRequest(BaseModel):
    variables: Dict[str, Any] = Field(default_factory=dict)
    title: Optional[str] = None
