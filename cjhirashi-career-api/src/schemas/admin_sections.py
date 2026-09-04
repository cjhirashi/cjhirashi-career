"""Schemas del catálogo de secciones del Admin."""
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class AdminSectionView(BaseModel):
    key: str
    label: str
    description: str
    sidebar_title: str
    sidebar_body: str
    is_default: bool = True


class AdminSectionViewUpdate(BaseModel):
    description: Optional[str] = None
    sidebar_title: Optional[str] = None
    sidebar_body: Optional[str] = None


class AdminSectionItem(BaseModel):
    id: str  # PK sec-N (ADR-021)
    system_name: str  # slug legible: dashboard, career-projects…
    label: str
    path: str
    section_type: str
    group: str = ""
    resource_key: Optional[str] = None
    related_tools: List[str] = []
    default_agent_profile_id: Optional[str] = None
    # feature 001: agente L2 del chat contextual del sidebar derecho (o None).
    agent_profile_id: Optional[str] = None
    agent_label: Optional[str] = None
    agent_is_default: bool = True
    sidebar_has_chat: bool = False
    sidebar_has_instructions: bool = False
    view_count: int
    views: List[AdminSectionView]


class AdminSectionUpdateRequest(BaseModel):
    agent_profile_id: Optional[str] = Field(
        default=None,
        description=(
            "Agente L2 del chat contextual. Omitir para no cambiar. "
            "String vacío restaura el default de código."
        ),
    )
    views: Optional[Dict[str, AdminSectionViewUpdate]] = None
