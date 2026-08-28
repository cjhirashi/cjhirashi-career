"""Jerarquía de secciones del Admin + vistas (ADR-022).

- ``GET /admin/nav-tree`` — árbol del sidebar izquierdo (grupos → L1 → L2 → L3 → vistas).
- Grupos y secciones: solo reorden y re-parent **dentro del mismo nivel** (el
  anidamiento entre niveles llega en el follow-up — ADR-022 §Seguimiento).
- Vistas: solo ``responsible_agent_profile_id`` (perfil **L2**) e ``instructions``.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from middleware.auth import get_current_user
from models.user import User
from schemas.admin_sections import (
    AdminViewItem,
    AdminViewUpdateRequest,
    GroupOrderRequest,
    NavTreeResponse,
    SectionDetail,
    SectionGroupItem,
    SectionGroupUpdateRequest,
    SectionListItem,
    SectionReorderRequest,
    SectionReparentRequest,
)
from services import section_catalog

router = APIRouter(prefix="/admin", tags=["Admin Sections"])


# ---------------------------------------------------------------------------
# nav-tree
# ---------------------------------------------------------------------------


@router.get("/nav-tree", response_model=NavTreeResponse, summary="Árbol del sidebar del Admin")
async def get_nav_tree(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await section_catalog.list_nav_tree(db)


# ---------------------------------------------------------------------------
# Grupos
# ---------------------------------------------------------------------------


@router.get("/section-groups", response_model=list[SectionGroupItem], summary="Grupos del sidebar")
async def list_section_groups(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await section_catalog.list_section_groups(db)


@router.put("/section-groups/order", response_model=list[SectionGroupItem], summary="Reordena los grupos")
async def reorder_section_groups(
    payload: GroupOrderRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await section_catalog.reorder_groups(db, payload.order)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.put("/section-groups/{grp_id}", response_model=SectionGroupItem, summary="Actualiza el orden de un grupo")
async def update_section_group(
    grp_id: str,
    payload: SectionGroupUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await section_catalog.update_group(db, grp_id, payload.sort_order)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown section group")


# ---------------------------------------------------------------------------
# Secciones
# ---------------------------------------------------------------------------


@router.put("/sections/order", response_model=list[SectionListItem], summary="Reordena secciones de un contenedor")
async def reorder_sections(
    payload: SectionReorderRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await section_catalog.reorder_sections(db, payload.container_id, payload.order)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


_LEVEL_KEYS = {"l1": 1, "l2": 2, "l3": 3}


@router.get("/sections/{key}", summary="Lista secciones de un nivel (l1|l2|l3) o detalle de una sección (s1-N…)")
async def list_or_get_section(
    key: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if key in _LEVEL_KEYS:
        return await section_catalog.list_sections(db, _LEVEL_KEYS[key])
    try:
        return await section_catalog.get_section(db, key)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown admin section")


@router.put("/sections/{sid}", response_model=SectionDetail, summary="Reordena / re-parenta una sección (mismo nivel)")
async def update_section(
    sid: str,
    payload: SectionReparentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await section_catalog.update_section(
            db,
            sid,
            sort_order=payload.sort_order,
            group_id=payload.group_id,
            parent_id=payload.parent_id,
        )
    except section_catalog.CycleError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown admin section")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


# ---------------------------------------------------------------------------
# Vistas
# ---------------------------------------------------------------------------


@router.get("/views", response_model=list[AdminViewItem], summary="Lista vistas (filtros opcionales)")
async def list_views(
    section_id: str | None = None,
    responsible: str | None = None,
    data_source: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await section_catalog.list_views(
            db, section_id=section_id, responsible=responsible, data_source=data_source
        )
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/views/{vw_id}", response_model=AdminViewItem, summary="Detalle de una vista (instructions completas)")
async def get_view(
    vw_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await section_catalog.get_view(db, vw_id)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown admin view")


@router.put("/views/{vw_id}", response_model=AdminViewItem, summary="Edita responsable L2 e instrucciones de una vista")
async def update_view(
    vw_id: str,
    payload: AdminViewUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    fields = payload.model_fields_set
    kwargs: dict = {}
    if "responsible_agent_profile_id" in fields:
        kwargs["responsible"] = payload.responsible_agent_profile_id or ""
    if "instructions" in fields:
        kwargs["instructions"] = payload.instructions or ""
    try:
        return await section_catalog.update_view(db, vw_id, **kwargs)
    except section_catalog.EmptyViewUpdateError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown admin view")
    except section_catalog.UnknownProfileError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"unknown agent profile: {exc.value}",
        )
    except section_catalog.ProfileNotLevel2Error as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"agent profile {exc.value} is not L2; contextual chat views can only "
                "be owned by a level-2 specialist"
            ),
        )
