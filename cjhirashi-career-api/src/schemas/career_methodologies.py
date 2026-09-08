"""
Pydantic schemas - Career domain (v2), Dominio 5: Metodologías Operativas.

Covers: operational_methodologies.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime


def _normalize_agent_profile_ids(value: Optional[List[str]]) -> Optional[List[str]]:
    if value is None:
        return None
    from services.bedrock.agent_profiles import known_agent_profile_ids

    cleaned: List[str] = []
    seen = set()
    unknown: List[str] = []
    known = known_agent_profile_ids()
    for item in value:
        agent_id = (item or "").strip()
        if not agent_id or agent_id in seen:
            continue
        if agent_id not in known:
            unknown.append(agent_id)
            continue
        seen.add(agent_id)
        cleaned.append(agent_id)
    if unknown:
        raise ValueError(f"agent_profile_ids desconocidos: {unknown}")
    return cleaned


def _normalize_section_ids(value: Optional[List[str]]) -> Optional[List[str]]:
    """Valida `sec-N` contra el catálogo de secciones del Admin (spec 004)."""
    if value is None:
        return None
    from services.admin_sections import known_section_ids

    cleaned: List[str] = []
    seen = set()
    unknown: List[str] = []
    known = known_section_ids()
    for item in value:
        sid = (item or "").strip()
        if not sid or sid in seen:
            continue
        if sid not in known:
            unknown.append(sid)
            continue
        seen.add(sid)
        cleaned.append(sid)
    if unknown:
        raise ValueError(f"section_ids desconocidos: {unknown}")
    return cleaned


# ============================================================================
# Metodologías operativas — esquemas CRUD
# ============================================================================

class OperationalMethodologyBase(BaseModel):
    title: str = Field(..., max_length=255)
    section: Optional[str] = Field(None, max_length=150)
    subsection: Optional[str] = Field(None, max_length=150)
    description: Optional[str] = None
    content: str
    agent_profile_ids: Optional[List[str]] = Field(
        None,
        description="IDs agent_* destinatarios (sólo L1/L3 desde spec 004). Vacío + section_ids vacío = compartida.",
    )
    section_ids: Optional[List[str]] = Field(
        None,
        description="IDs sec-N de secciones del Admin a las que está ligada (spec 004). Un L2 ligado a alguna la recibe.",
    )
    notes: Optional[str] = None


class OperationalMethodologyCreate(OperationalMethodologyBase):
    @field_validator("agent_profile_ids")
    @classmethod
    def validate_agent_profile_ids(cls, value: Optional[List[str]]) -> Optional[List[str]]:
        return _normalize_agent_profile_ids(value)

    @field_validator("section_ids")
    @classmethod
    def validate_section_ids(cls, value: Optional[List[str]]) -> Optional[List[str]]:
        return _normalize_section_ids(value)


class OperationalMethodologyUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    section: Optional[str] = None
    subsection: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    agent_profile_ids: Optional[List[str]] = None
    section_ids: Optional[List[str]] = None
    notes: Optional[str] = None

    @field_validator("agent_profile_ids")
    @classmethod
    def validate_agent_profile_ids(cls, value: Optional[List[str]]) -> Optional[List[str]]:
        return _normalize_agent_profile_ids(value)

    @field_validator("section_ids")
    @classmethod
    def validate_section_ids(cls, value: Optional[List[str]]) -> Optional[List[str]]:
        return _normalize_section_ids(value)


class OperationalMethodologyResponse(OperationalMethodologyBase):
    # No agent_profile_ids validation here (unlike Create/Update): a row whose
    # ids no longer match the current agent catalog must still be readable,
    # or every GET on this resource 500s until someone edits that one record.
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
