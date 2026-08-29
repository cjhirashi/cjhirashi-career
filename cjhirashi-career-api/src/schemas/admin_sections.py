"""Schemas de la jerarquía de secciones del Admin + vistas (ADR-022; CRUD ADR-023).

Reemplaza el contrato plano ``sec-N`` de ADR-021. Desde ADR-023 (corrección) la
API expone CRUD completo de grupos y secciones (crear, editar, borrar, mover de
nivel), además del reorder/re-parent original y la edición de los 2 campos del
operador de cada vista (``responsible_agent_profile_id`` L2 + ``instructions``)
más la reasignación de sección dueña de una vista.
"""
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from services.section_catalog import VISIBILITY_LEVELS

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
    visibility_level: str = "standard"


class NavSection(BaseModel):
    id: str
    level: int
    system_name: str
    label: str
    path: Optional[str] = None
    section_type: str
    sort_order: int
    origin: str = "code"
    visibility_level: str = "standard"
    has_layout: bool = False
    view_count: int = 0
    views: List[NavView] = []
    children: List["NavSection"] = []


class NavGroup(BaseModel):
    id: str
    system_name: str
    name: str
    sort_order: int
    visibility_level: str = "standard"
    sections: List[NavSection] = []


class NavTreeResponse(BaseModel):
    groups: List[NavGroup] = []
    generated_at: str


# ---------------------------------------------------------------------------
# Grupos (GET/POST/PUT/DELETE /admin/section-groups)
# ---------------------------------------------------------------------------


class SectionGroupItem(BaseModel):
    id: str
    system_name: str
    name: str
    sort_order: int
    origin: str = "code"
    visibility_level: str = "standard"


class GroupOrderRequest(BaseModel):
    order: List[str] = Field(..., description="IDs grp-N en el orden deseado (lista completa)")


class SectionGroupUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sort_order: int


class SectionGroupCreateRequest(BaseModel):
    """POST /admin/section-groups. ``system_name == 'admin'`` siempre 400."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=120)
    system_name: str = Field(
        ..., min_length=1, max_length=60, pattern=r"^[a-z][a-z0-9-]*$"
    )
    sort_order: Optional[int] = None
    visibility_level: str = "standard"

    @model_validator(mode="after")
    def _check_visibility(self) -> "SectionGroupCreateRequest":
        if self.visibility_level not in VISIBILITY_LEVELS:
            raise ValueError(f"visibility_level debe ser uno de {VISIBILITY_LEVELS}")
        return self


# ---------------------------------------------------------------------------
# Secciones (GET/POST/PUT/DELETE /admin/sections/*)
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
    visibility_level: str = "standard"
    group_id: Optional[str] = None
    parent_id: Optional[str] = None
    view_count: int = 0


class SectionDetail(SectionListItem):
    views: List[NavView] = []


class SectionCreateRequest(BaseModel):
    """POST /admin/sections. Exactamente uno de group_id/parent_id según level."""

    model_config = ConfigDict(extra="forbid")

    level: int = Field(..., ge=1, le=3)
    label: str = Field(..., min_length=1, max_length=120)
    system_name: str = Field(..., min_length=1, max_length=80)
    path: Optional[str] = None
    section_type: str
    group_id: Optional[str] = None
    parent_id: Optional[str] = None
    visibility_level: str = "standard"

    @model_validator(mode="after")
    def _check_shape(self) -> "SectionCreateRequest":
        if self.visibility_level not in VISIBILITY_LEVELS:
            raise ValueError(f"visibility_level debe ser uno de {VISIBILITY_LEVELS}")
        if self.level == 1:
            if self.group_id is None or self.parent_id is not None:
                raise ValueError("level=1 requiere group_id y no admite parent_id")
        elif self.level in (2, 3):
            if self.parent_id is None or self.group_id is not None:
                raise ValueError("level in (2,3) requiere parent_id y no admite group_id")
        else:
            raise ValueError("level debe ser 1, 2 o 3")
        return self


class SectionUpdateRequest(BaseModel):
    """PUT /admin/sections/{sid}. Todos opcionales; re-parent solo dentro del mismo nivel.

    El cambio de nivel (L1<->L2<->L3) NO va aquí — ver ``SectionMoveRequest``.
    """

    model_config = ConfigDict(extra="forbid")

    label: Optional[str] = Field(default=None, min_length=1, max_length=120)
    system_name: Optional[str] = Field(default=None, min_length=1, max_length=80)
    path: Optional[str] = None
    section_type: Optional[str] = None
    sort_order: Optional[int] = None
    visibility_level: Optional[str] = None
    group_id: Optional[str] = Field(default=None, description="Solo L1: mover a otro grupo")
    parent_id: Optional[str] = Field(
        default=None, description="Solo L2/L3: mover a otro padre del mismo nivel"
    )

    @model_validator(mode="after")
    def _check_visibility(self) -> "SectionUpdateRequest":
        if self.visibility_level is not None and self.visibility_level not in VISIBILITY_LEVELS:
            raise ValueError(f"visibility_level debe ser uno de {VISIBILITY_LEVELS}")
        return self


class SectionReorderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    container_id: str = Field(..., description="grp-N | s1-N | s2-N — contenedor de las secciones a ordenar")
    order: List[str] = Field(..., description="IDs de las secciones hijas en el orden deseado")


class SectionMoveRequest(BaseModel):
    """POST /admin/sections/{sid}/move. Mueve una sección entre niveles (L1<->L2<->L3)."""

    model_config = ConfigDict(extra="forbid")

    target_level: int = Field(..., ge=1, le=3)
    target_parent_id: str = Field(
        ..., description="grp-N si target_level==1, s1-N si ==2, s2-N si ==3"
    )


class SectionMoveResponse(SectionDetail):
    previous_id: str


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
    visibility_level: str = "standard"


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
    owner_l1_id: Optional[str] = Field(
        default=None, description="Reasigna la vista a esta sección L1"
    )
    owner_l2_id: Optional[str] = Field(
        default=None, description="Reasigna la vista a esta sección L2"
    )
    owner_l3_id: Optional[str] = Field(
        default=None, description="Reasigna la vista a esta sección L3"
    )


NavSection.model_rebuild()
