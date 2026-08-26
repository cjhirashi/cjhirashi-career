"""
Career domain (v2), Dominio 3: Presencia Digital.

Aggregates CRUD routers for: publications, linkedin-profile, github-profile,
portal-home, portal-about, portal-contact. Plus a live (non-CRUD) endpoint
that fetches the connected GitHub username's public repos.
"""
# ============================================================================
# Imports
# ============================================================================
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from middleware.auth import get_current_user
from models.user import User
from models.publication import Publication
from models.linkedin_profile import LinkedInProfile
from models.github_profile import GitHubProfile
from models.portal_home import PortalHome
from models.portal_about import PortalAbout
from models.portal_contact import PortalContact

from schemas.career_digital import (
    PublicationCreate, PublicationUpdate, PublicationResponse,
    LinkedInProfileCreate, LinkedInProfileUpdate, LinkedInProfileResponse,
    GitHubProfileCreate, GitHubProfileUpdate, GitHubProfileResponse,
    PortalHomeCreate, PortalHomeUpdate, PortalHomeResponse,
    PortalAboutCreate, PortalAboutUpdate, PortalAboutResponse,
    PortalContactCreate, PortalContactUpdate, PortalContactResponse,
)

from routes.career_common import build_crud_router
from services import github_service
from services.github_service import GitHubError

# ============================================================================
# Router principal
# ============================================================================
router = APIRouter(prefix="/career", tags=["Career - Digital Presence"])


# ============================================================================
# Endpoint: repositorios GitHub (consulta en vivo)
# ============================================================================
@router.get("/github-profile/repos", summary="List the connected GitHub username's public repos (live)")
async def list_github_repos(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(GitHubProfile).where(GitHubProfile.user_id == current_user.id))
    profile = result.scalar_one_or_none()
    if profile is None or not profile.username:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Configura tu username de GitHub en el perfil de GitHub primero",
        )
    try:
        return await github_service.list_public_repos(profile.username)
    except GitHubError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

# ============================================================================
# Publicaciones y perfiles sociales
# ============================================================================
router.include_router(build_crud_router(
    prefix="/publications", tags=["Career - Digital Presence"], model=Publication,
    create_schema=PublicationCreate, update_schema=PublicationUpdate,
    response_schema=PublicationResponse, entity_name="publication",
))

router.include_router(build_crud_router(
    prefix="/linkedin-profile", tags=["Career - Digital Presence"], model=LinkedInProfile,
    create_schema=LinkedInProfileCreate, update_schema=LinkedInProfileUpdate,
    response_schema=LinkedInProfileResponse, entity_name="LinkedIn profile",
))

router.include_router(build_crud_router(
    prefix="/github-profile", tags=["Career - Digital Presence"], model=GitHubProfile,
    create_schema=GitHubProfileCreate, update_schema=GitHubProfileUpdate,
    response_schema=GitHubProfileResponse, entity_name="GitHub profile",
))

# ============================================================================
# Contenido del portal público
# ============================================================================
router.include_router(build_crud_router(
    prefix="/portal-home", tags=["Career - Digital Presence"], model=PortalHome,
    create_schema=PortalHomeCreate, update_schema=PortalHomeUpdate,
    response_schema=PortalHomeResponse, entity_name="portal home content",
))

router.include_router(build_crud_router(
    prefix="/portal-about", tags=["Career - Digital Presence"], model=PortalAbout,
    create_schema=PortalAboutCreate, update_schema=PortalAboutUpdate,
    response_schema=PortalAboutResponse, entity_name="portal about content",
))

router.include_router(build_crud_router(
    prefix="/portal-contact", tags=["Career - Digital Presence"], model=PortalContact,
    create_schema=PortalContactCreate, update_schema=PortalContactUpdate,
    response_schema=PortalContactResponse, entity_name="portal contact content",
))
