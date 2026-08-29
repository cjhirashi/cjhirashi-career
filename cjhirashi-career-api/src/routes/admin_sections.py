"""Jerarquía de secciones del Admin + vistas (ADR-022; CRUD ADR-023 corrección).

- ``GET /admin/nav-tree`` — árbol del sidebar izquierdo (grupos → L1 → L2 → L3 → vistas).
- Grupos y secciones: CRUD completo (crear, editar, borrar, reorder, re-parent
  dentro del mismo nivel, mover entre niveles) — ADR-023 (corrección).
- Vistas: ``responsible_agent_profile_id`` (perfil **L2**), ``instructions`` y
  reasignación de sección dueña (``owner_l{1,2,3}_id``).
- Gate de visibilidad: todas las mutaciones que tocan el subárbol del grupo
  protegido ``admin`` (o cualquier fila con ``visibility_level="superuser"``)
  exigen ``current_user.is_superuser`` — ver ``services/section_catalog.py``.
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
    SectionCreateRequest,
    SectionDetail,
    SectionGroupCreateRequest,
    SectionGroupItem,
    SectionGroupUpdateRequest,
    SectionListItem,
    SectionMoveRequest,
    SectionMoveResponse,
    SectionReorderRequest,
    SectionUpdateRequest,
)
from services import section_catalog

router = APIRouter(prefix="/admin", tags=["Admin Sections"])


def _http_error(exc: Exception) -> HTTPException:
    """Traduce las excepciones de ``section_catalog`` al status HTTP del contrato."""
    if isinstance(exc, section_catalog.ForbiddenVisibilityError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, section_catalog.ProtectedResourceError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, (section_catalog.HasChildrenError, section_catalog.HasViewsError)):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    if isinstance(exc, section_catalog.DuplicateError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    if isinstance(exc, section_catalog.CycleError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    if isinstance(exc, KeyError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc) or "Not found")
    if isinstance(exc, ValueError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    raise exc


# ---------------------------------------------------------------------------
# nav-tree
# ---------------------------------------------------------------------------


@router.get("/nav-tree", response_model=NavTreeResponse, summary="Árbol del sidebar del Admin")
async def get_nav_tree(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await section_catalog.list_nav_tree(db, is_superuser=bool(current_user.is_superuser))


# ---------------------------------------------------------------------------
# Grupos
# ---------------------------------------------------------------------------


@router.get("/section-groups", response_model=list[SectionGroupItem], summary="Grupos del sidebar")
async def list_section_groups(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await section_catalog.list_section_groups(
        db, is_superuser=bool(current_user.is_superuser)
    )


@router.post(
    "/section-groups",
    response_model=SectionGroupItem,
    status_code=status.HTTP_201_CREATED,
    summary="Crea un grupo",
)
async def create_section_group(
    payload: SectionGroupCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await section_catalog.create_group(
            db,
            name=payload.name,
            system_name=payload.system_name,
            sort_order=payload.sort_order,
            visibility_level=payload.visibility_level,
        )
    except Exception as exc:  # noqa: BLE001 - traducido por _http_error
        raise _http_error(exc)


@router.delete(
    "/section-groups/{grp_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Borra un grupo (sin secciones hijas)",
)
async def delete_section_group(
    grp_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await section_catalog.delete_group(
            db, grp_id, is_superuser=bool(current_user.is_superuser)
        )
    except Exception as exc:  # noqa: BLE001
        raise _http_error(exc)


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


@router.post(
    "/sections",
    response_model=SectionDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Crea una sección L1/L2/L3",
)
async def create_section(
    payload: SectionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await section_catalog.create_section(
            db,
            level=payload.level,
            label=payload.label,
            system_name=payload.system_name,
            section_type=payload.section_type,
            path=payload.path,
            group_id=payload.group_id,
            parent_id=payload.parent_id,
            visibility_level=payload.visibility_level,
            is_superuser=bool(current_user.is_superuser),
        )
    except Exception as exc:  # noqa: BLE001
        raise _http_error(exc)


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
    is_superuser = bool(current_user.is_superuser)
    if key in _LEVEL_KEYS:
        return await section_catalog.list_sections(db, _LEVEL_KEYS[key], is_superuser=is_superuser)
    try:
        return await section_catalog.get_section(db, key, is_superuser=is_superuser)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown admin section")


@router.put("/sections/{sid}", response_model=SectionDetail, summary="Edita/reordena/re-parenta una sección (mismo nivel)")
async def update_section(
    sid: str,
    payload: SectionUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    kwargs = payload.model_dump(exclude_unset=True)
    try:
        return await section_catalog.update_section(
            db,
            sid,
            is_superuser=bool(current_user.is_superuser),
            **kwargs,
        )
    except Exception as exc:  # noqa: BLE001
        raise _http_error(exc)


@router.delete(
    "/sections/{sid}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Borra una sección (sin hijas ni vistas propias)",
)
async def delete_section(
    sid: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await section_catalog.delete_section(
            db, sid, is_superuser=bool(current_user.is_superuser)
        )
    except Exception as exc:  # noqa: BLE001
        raise _http_error(exc)


@router.post(
    "/sections/{sid}/move",
    response_model=SectionMoveResponse,
    summary="Mueve una sección entre niveles (L1<->L2<->L3, sin hijas propias)",
)
async def move_section(
    sid: str,
    payload: SectionMoveRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await section_catalog.move_section(
            db,
            sid,
            target_level=payload.target_level,
            target_parent_id=payload.target_parent_id,
            is_superuser=bool(current_user.is_superuser),
        )
    except Exception as exc:  # noqa: BLE001
        raise _http_error(exc)


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


@router.put(
    "/views/{vw_id}",
    response_model=AdminViewItem,
    summary="Edita responsable L2, instrucciones y/o reasigna la sección dueña de una vista",
)
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
    if "owner_l1_id" in fields:
        kwargs["owner_l1_id"] = payload.owner_l1_id
    if "owner_l2_id" in fields:
        kwargs["owner_l2_id"] = payload.owner_l2_id
    if "owner_l3_id" in fields:
        kwargs["owner_l3_id"] = payload.owner_l3_id
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
    except section_catalog.UnknownSectionTargetError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"unknown target section: {exc.value}",
        )
    except section_catalog.DuplicateViewKeyError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
