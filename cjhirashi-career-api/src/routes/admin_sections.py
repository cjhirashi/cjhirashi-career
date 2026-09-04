"""Catálogo de secciones del Admin — tipo, agente de dominio, vistas e instrucciones."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from middleware.auth import get_current_user
from models.user import User
from schemas.admin_sections import AdminSectionItem, AdminSectionUpdateRequest
from services import section_catalog
from services.admin_sections import get_section_spec, is_l2
from services.bedrock.agent_profiles import get_profile

router = APIRouter(prefix="/admin", tags=["Admin Sections"])


@router.get("/sections", response_model=list[AdminSectionItem], summary="Catálogo de secciones del Admin")
async def list_admin_sections(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await section_catalog.list_sections(db)


@router.get("/sections/{section_id}", response_model=AdminSectionItem, summary="Detalle de una sección")
async def get_admin_section(
    section_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        get_section_spec(section_id)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown admin section")
    return await section_catalog.get_section(db, section_id)


@router.put("/sections/{section_id}", response_model=AdminSectionItem, summary="Actualiza dominio e instrucciones de una sección")
async def update_admin_section(
    section_id: str,
    payload: AdminSectionUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        get_section_spec(section_id)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown admin section")
    agent_id = payload.agent_profile_id
    clear_agent = False
    if agent_id is not None:
        if agent_id == "":
            clear_agent = True
            agent_id = None
        else:
            try:
                get_profile(agent_id)
            except KeyError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown agent profile"
                )
            if not is_l2(agent_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Agent profile is not L2",
                )
    views = None
    if payload.views is not None:
        views = {
            key: item.model_dump(exclude_none=True) for key, item in payload.views.items()
        }
    try:
        return await section_catalog.update_section(
            db,
            section_id,
            agent_profile_id=agent_id,
            clear_agent=clear_agent,
            views=views,
        )
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
