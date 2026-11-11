"""
Pydantic schemas - Career domain (v2), Dominio 5: Metodologías Operativas.

Covers: operational_methodologies.
"""
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime


# ============================================================================
# Metodologías operativas — esquemas CRUD
# ============================================================================

class OperationalMethodologyBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    content: str


class OperationalMethodologyCreate(OperationalMethodologyBase):
    pass


class OperationalMethodologyUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    content: Optional[str] = None


class OperationalMethodologyResponse(OperationalMethodologyBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
