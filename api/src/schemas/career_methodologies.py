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
    notes: Optional[str] = None


class OperationalMethodologyCreate(OperationalMethodologyBase):
    pass
    notes: Optional[str] = None


class OperationalMethodologyUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    section: Optional[str] = None
    subsection: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    notes: Optional[str] = None


class OperationalMethodologyResponse(OperationalMethodologyBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    notes: Optional[str] = None

    class Config:
        from_attributes = True
