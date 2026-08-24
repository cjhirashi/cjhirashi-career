"""
Pydantic schemas - Career domain (v2), Dominio 4: Soporte.

Covers: tags.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TagBase(BaseModel):
    tag_name: str = Field(..., max_length=100)
    entity_type: Optional[str] = Field(None, max_length=100)
    color_hex: Optional[str] = Field(None, max_length=7)
    is_active: bool = True
    notes: Optional[str] = None


class TagCreate(TagBase):
    pass
    notes: Optional[str] = None


class TagUpdate(BaseModel):
    tag_name: Optional[str] = Field(None, max_length=100)
    entity_type: Optional[str] = None
    color_hex: Optional[str] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class TagResponse(TagBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    notes: Optional[str] = None

    class Config:
        from_attributes = True
