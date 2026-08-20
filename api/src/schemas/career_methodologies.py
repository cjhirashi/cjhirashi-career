"""
Pydantic schemas - Career domain (v2), Dominio 5: Metodologías Operativas.

Covers: operational_methodologies.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class OperationalMethodologyBase(BaseModel):
    title: str = Field(..., max_length=255)
    section: Optional[str] = Field(None, max_length=150)
    subsection: Optional[str] = Field(None, max_length=150)
    description: Optional[str] = None
    content: str


class OperationalMethodologyCreate(OperationalMethodologyBase):
    pass


class OperationalMethodologyUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    section: Optional[str] = None
    subsection: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None


class OperationalMethodologyResponse(OperationalMethodologyBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
