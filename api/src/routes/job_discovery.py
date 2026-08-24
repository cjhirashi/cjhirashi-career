"""
Job discovery endpoints (not generic CRUD).

Preview-then-save: /run and /import-url never write vacancies.
"""
# ============================================================================
# Imports
# ============================================================================
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from middleware.auth import get_current_user
from models.user import User
from schemas.job_discovery import (
    ImportUrlRequest,
    JobDiscoveryRunRequest,
    JobDiscoveryRunResponse,
    JobListingSchema,
    ProviderErrorSchema,
    ProviderStatusSchema,
    SaveListingsRequest,
    SaveListingsResponse,
)
from services.job_discovery import (
    import_vacancy_url,
    listing_to_dict,
    providers as list_providers,
    run_discovery,
    save_listings,
)
from services.job_discovery.preview_store import append_preview

# ============================================================================
# Router principal
# ============================================================================
router = APIRouter(prefix="/career/job-discoveries", tags=["Career - Job Discovery"])


# ============================================================================
# Endpoints: proveedores, búsqueda, importación y guardado
# ============================================================================
@router.get("/providers", response_model=List[ProviderStatusSchema])
async def get_providers(current_user: User = Depends(get_current_user)):
    del current_user
    return list_providers()


@router.post("/run", response_model=JobDiscoveryRunResponse)
async def run_job_discovery(
    payload: JobDiscoveryRunRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await run_discovery(
            db,
            current_user.id,
            query_text=payload.query,
            location=payload.location,
            providers=payload.providers,
            target_role_id=payload.target_role_id,
            include_company_boards=payload.include_company_boards,
            remote=payload.remote,
            session_key="admin",
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return JobDiscoveryRunResponse(
        query=result.query,
        location=result.location,
        listings=[JobListingSchema(**listing_to_dict(item)) for item in result.listings],
        errors=[ProviderErrorSchema(provider=e.provider, message=e.message) for e in result.errors],
    )


@router.post("/import-url", response_model=JobListingSchema)
async def import_job_url(
    payload: ImportUrlRequest,
    current_user: User = Depends(get_current_user),
):
    listing = await import_vacancy_url(payload.url)
    remembered = append_preview(current_user.id, "admin", listing_to_dict(listing))
    listing.ref = remembered["ref"]
    return JobListingSchema(**listing_to_dict(listing))


@router.post("/save", response_model=SaveListingsResponse)
async def save_job_listings(
    payload: SaveListingsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await save_listings(
        db,
        current_user.id,
        [item.model_dump() for item in payload.listings],
        target_role_id=payload.target_role_id,
    )
    return SaveListingsResponse(**result)
