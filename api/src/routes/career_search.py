"""
Career domain (v2), Dominio 2: Operativa de Búsqueda.

Aggregates CRUD routers for: fit_scoring_factors, market_segments,
role_narratives, search_plans, networking_contacts, target_companies,
vacancies, cv_versions, cover_letter_versions, applications,
application_interactions, interviews, contact_interactions,
networking_activities. Also hand-writes cv_versions' one non-CRUD endpoint
(PDF export), on top of the CRUD router `build_crud_router` gives it.
"""
import re

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from middleware.auth import get_current_user
from models.user import User
from repositories.career_repository import CareerRepository
from services.pdf_service import PDFGeneratorError, generate_markdown_document

from models.fit_scoring_factor import FitScoringFactor
from models.market_segment import MarketSegment
from models.role_narrative import RoleNarrative
from models.search_plan import SearchPlan
from models.networking_contact import NetworkingContact
from models.target_company import TargetCompany
from models.vacancy import Vacancy
from models.cv_version import CVVersion
from models.cover_letter_version import CoverLetterVersion
from models.application import Application
from models.application_interaction import ApplicationInteraction
from models.interview import Interview
from models.contact_interaction import ContactInteraction
from models.networking_activity import NetworkingActivity

from schemas.career_search import (
    FitScoringFactorCreate, FitScoringFactorUpdate, FitScoringFactorResponse,
    MarketSegmentCreate, MarketSegmentUpdate, MarketSegmentResponse,
    RoleNarrativeCreate, RoleNarrativeUpdate, RoleNarrativeResponse,
    SearchPlanCreate, SearchPlanUpdate, SearchPlanResponse,
    NetworkingContactCreate, NetworkingContactUpdate, NetworkingContactResponse,
    TargetCompanyCreate, TargetCompanyUpdate, TargetCompanyResponse,
    VacancyCreate, VacancyUpdate, VacancyResponse,
    CVVersionCreate, CVVersionUpdate, CVVersionResponse,
    CoverLetterVersionCreate, CoverLetterVersionUpdate, CoverLetterVersionResponse,
    ApplicationCreate, ApplicationUpdate, ApplicationResponse,
    ApplicationInteractionCreate, ApplicationInteractionUpdate, ApplicationInteractionResponse,
    InterviewCreate, InterviewUpdate, InterviewResponse,
    ContactInteractionCreate, ContactInteractionUpdate, ContactInteractionResponse,
    NetworkingActivityCreate, NetworkingActivityUpdate, NetworkingActivityResponse,
)

from routes.career_common import build_crud_router

router = APIRouter(prefix="/career", tags=["Career - Search"])

router.include_router(build_crud_router(
    prefix="/fit-scoring-factors", tags=["Career - Search"], model=FitScoringFactor,
    create_schema=FitScoringFactorCreate, update_schema=FitScoringFactorUpdate,
    response_schema=FitScoringFactorResponse, entity_name="fit scoring factor",
))

router.include_router(build_crud_router(
    prefix="/market-segments", tags=["Career - Search"], model=MarketSegment,
    create_schema=MarketSegmentCreate, update_schema=MarketSegmentUpdate,
    response_schema=MarketSegmentResponse, entity_name="market segment",
))

router.include_router(build_crud_router(
    prefix="/role-narratives", tags=["Career - Search"], model=RoleNarrative,
    create_schema=RoleNarrativeCreate, update_schema=RoleNarrativeUpdate,
    response_schema=RoleNarrativeResponse, entity_name="role narrative",
))

router.include_router(build_crud_router(
    prefix="/search-plans", tags=["Career - Search"], model=SearchPlan,
    create_schema=SearchPlanCreate, update_schema=SearchPlanUpdate,
    response_schema=SearchPlanResponse, entity_name="search plan",
))

router.include_router(build_crud_router(
    prefix="/networking-contacts", tags=["Career - Search"], model=NetworkingContact,
    create_schema=NetworkingContactCreate, update_schema=NetworkingContactUpdate,
    response_schema=NetworkingContactResponse, entity_name="networking contact",
))

router.include_router(build_crud_router(
    prefix="/target-companies", tags=["Career - Search"], model=TargetCompany,
    create_schema=TargetCompanyCreate, update_schema=TargetCompanyUpdate,
    response_schema=TargetCompanyResponse, entity_name="target company",
))

router.include_router(build_crud_router(
    prefix="/vacancies", tags=["Career - Search"], model=Vacancy,
    create_schema=VacancyCreate, update_schema=VacancyUpdate,
    response_schema=VacancyResponse, entity_name="vacancy",
))

router.include_router(build_crud_router(
    prefix="/cv-versions", tags=["Career - Search"], model=CVVersion,
    create_schema=CVVersionCreate, update_schema=CVVersionUpdate,
    response_schema=CVVersionResponse, entity_name="CV version",
    # PDF-content table: the agent should read a CV version's Markdown
    # `content` straight from Postgres, not from a copy in Qdrant.
    vectorize=False,
))

# Repository instance dedicated to the endpoint below - separate from the one
# `build_crud_router` builds internally (not exposed outside that factory),
# but identical in behaviour: `get_for_user` enforces the same row-level
# ownership check (404 if the row doesn't belong to `current_user`) as every
# other cv-versions endpoint.
_cv_version_repo = CareerRepository(CVVersion, resource_key="cv-versions", vectorize=False)


@router.post(
    "/cv-versions/{cv_version_id}/pdf",
    tags=["Career - Search"],
    summary="Render a CV version's Markdown content into a downloadable PDF",
)
async def generate_cv_version_pdf(
    cv_version_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cv_version = await _cv_version_repo.get_for_user(db, current_user.id, cv_version_id)
    if cv_version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CV version not found")

    if not cv_version.content or not cv_version.content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La versión de CV no tiene contenido para generar el PDF",
        )

    try:
        pdf_bytes = await generate_markdown_document(cv_version.title, cv_version.content)
    except PDFGeneratorError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    safe_title = re.sub(r"[^a-zA-Z0-9]+", "-", cv_version.title.strip()).strip("-") or "cv"
    filename = f"{safe_title}.pdf"

    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


router.include_router(build_crud_router(
    prefix="/cover-letter-versions", tags=["Career - Search"], model=CoverLetterVersion,
    create_schema=CoverLetterVersionCreate, update_schema=CoverLetterVersionUpdate,
    response_schema=CoverLetterVersionResponse, entity_name="cover letter version",
))

router.include_router(build_crud_router(
    prefix="/applications", tags=["Career - Search"], model=Application,
    create_schema=ApplicationCreate, update_schema=ApplicationUpdate,
    response_schema=ApplicationResponse, entity_name="application",
))

router.include_router(build_crud_router(
    prefix="/application-interactions", tags=["Career - Search"], model=ApplicationInteraction,
    create_schema=ApplicationInteractionCreate, update_schema=ApplicationInteractionUpdate,
    response_schema=ApplicationInteractionResponse, entity_name="application interaction",
))

router.include_router(build_crud_router(
    prefix="/interviews", tags=["Career - Search"], model=Interview,
    create_schema=InterviewCreate, update_schema=InterviewUpdate,
    response_schema=InterviewResponse, entity_name="interview",
))

router.include_router(build_crud_router(
    prefix="/contact-interactions", tags=["Career - Search"], model=ContactInteraction,
    create_schema=ContactInteractionCreate, update_schema=ContactInteractionUpdate,
    response_schema=ContactInteractionResponse, entity_name="contact interaction",
))

router.include_router(build_crud_router(
    prefix="/networking-activities", tags=["Career - Search"], model=NetworkingActivity,
    create_schema=NetworkingActivityCreate, update_schema=NetworkingActivityUpdate,
    response_schema=NetworkingActivityResponse, entity_name="networking activity",
))
