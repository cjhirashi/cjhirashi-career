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


class TagCreate(TagBase):
    pass


class TagUpdate(BaseModel):
    tag_name: Optional[str] = Field(None, max_length=100)
    entity_type: Optional[str] = None
    color_hex: Optional[str] = None
    is_active: Optional[bool] = None


class TagResponse(TagBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
