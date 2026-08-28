"""Schemas de la jerarquía de secciones del Admin + vistas (ADR-022).

Reemplaza el contrato plano ``sec-N`` de ADR-021. La estructura (grupos → L1 →
L2 → L3 → vistas) es de solo lectura vía la API (la siembra el código); la API
solo reordena/re-parenta secciones y edita los 2 campos del operador de cada
vista (``responsible_agent_profile_id`` L2 + ``instructions``).
"""
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# nav-tree (GET /admin/nav-tree)
# ---------------------------------------------------------------------------


class NavView(BaseModel):
    id: str
    key: str
    label: str
    sort_order: int
    data_source: str
    resource_key: Optional[str] = None
    has_controls_window: bool = False
    tool_names: List[str] = []
    responsible_agent_profile_id: Optional[str] = None
    has_instructions: bool = False
    chat_enabled: bool = False


class NavSection(BaseModel):
    id: str
    level: int
    system_name: str
    label: str
    path: Optional[str] = None
    section_type: str
    sort_order: int
    origin: str = "code"
    has_layout: bool = False
    view_count: int = 0
    views: List[NavView] = []
    children: List["NavSection"] = []


class NavGroup(BaseModel):
    id: str
    system_name: str
    name: str
    sort_order: int
    sections: List[NavSection] = []


class NavTreeResponse(BaseModel):
    groups: List[NavGroup] = []
    generated_at: str


# ---------------------------------------------------------------------------
# Grupos (GET/PUT /admin/section-groups)
# ---------------------------------------------------------------------------


class SectionGroupItem(BaseModel):
    id: str
    system_name: str
    name: str
    sort_order: int


class GroupOrderRequest(BaseModel):
    order: List[str] = Field(..., description="IDs grp-N en el orden deseado (lista completa)")


class SectionGroupUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sort_order: int


# ---------------------------------------------------------------------------
# Secciones (GET/PUT /admin/sections/*)
# ---------------------------------------------------------------------------


class SectionListItem(BaseModel):
    id: str
    level: int
    system_name: str
    label: str
    path: Optional[str] = None
    section_type: str
    sort_order: int
    origin: str = "code"
    group_id: Optional[str] = None
    parent_id: Optional[str] = None
    view_count: int = 0


class SectionDetail(SectionListItem):
    views: List[NavView] = []


class SectionReparentRequest(BaseModel):
    """PUT /admin/sections/{sid}. Todos opcionales; re-parent solo dentro del mismo nivel."""

    model_config = ConfigDict(extra="forbid")

    sort_order: Optional[int] = None
    group_id: Optional[str] = Field(default=None, description="Solo L1: mover a otro grupo")
    parent_id: Optional[str] = Field(
        default=None, description="Solo L2/L3: mover a otro padre del mismo nivel"
    )


class SectionReorderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    container_id: str = Field(..., description="grp-N | s1-N | s2-N — contenedor de las secciones a ordenar")
    order: List[str] = Field(..., description="IDs de las secciones hijas en el orden deseado")


# ---------------------------------------------------------------------------
# Vistas (GET/PUT /admin/views/*)
# ---------------------------------------------------------------------------


class AdminViewOwner(BaseModel):
    level: int
    section_id: str
    section_system_name: str
    section_label: str
    section_path: Optional[str] = None


class AdminViewItem(BaseModel):
    id: str
    owner: AdminViewOwner
    key: str
    label: str
    sort_order: int
    data_source: str
    resource_key: Optional[str] = None
    has_controls_window: bool = False
    tool_names: List[str] = []
    responsible_agent_profile_id: Optional[str] = None
    responsible_agent_label: Optional[str] = None
    responsible_is_l2: bool = False
    instructions: Optional[str] = None
    chat_enabled: bool = False
    instructions_enabled: bool = False


class AdminViewUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    responsible_agent_profile_id: Optional[str] = Field(
        default=None,
        description='System name de un perfil L2. "" quita el responsable. Omitir = sin cambio.',
    )
    instructions: Optional[str] = Field(
        default=None,
        description='Texto del panel del sidebar. "" borra el panel. Omitir = sin cambio.',
    )


NavSection.model_rebuild()
