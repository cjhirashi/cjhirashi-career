"""
Schemas de Pydantic para modelos de documento.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any, List


class DocumentBase(BaseModel):
    """Schema base de documento."""
    type: str = Field(..., min_length=1, max_length=50)
    title: Optional[str] = Field(None, max_length=255)
    data: Dict[str, Any] = Field(..., description="Contenido del documento en formato JSON")


class DocumentCreate(DocumentBase):
    """Schema para creación de documento."""
    pass


class DocumentUpdate(BaseModel):
    """Schema para actualización de documento."""
    type: Optional[str] = Field(None, min_length=1, max_length=50)
    title: Optional[str] = Field(None, max_length=255)
    data: Optional[Dict[str, Any]] = Field(None, description="Contenido del documento en formato JSON")


class DocumentResponse(DocumentBase):
    """Schema para respuesta de documento."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Schema para lista de documentos."""
    total: int
    documents: List[DocumentResponse]
