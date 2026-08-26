"""Pydantic schemas for job discovery endpoints."""
from datetime import date
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


# ============================================================================
# Tipos y esquemas base
# ============================================================================

ListingKind = Literal["job", "search_url"]


class JobListingSchema(BaseModel):
    company: str
    exact_role: str
    vacancy_url: str
    source: str
    listing_kind: ListingKind = "job"
    via: Optional[str] = None
    found_date: Optional[date] = None
    location: Optional[str] = None
    salary_text: Optional[str] = None
    remote: Optional[bool] = None
    snippet: Optional[str] = None
    external_id: Optional[str] = None
    already_saved: bool = False
    ref: Optional[str] = None


class ProviderStatusSchema(BaseModel):
    id: str
    label: str
    enabled: bool
    reason: Optional[str] = None
    listing_kind: ListingKind = "job"


class ProviderErrorSchema(BaseModel):
    provider: str
    message: str


# ============================================================================
# Descubrimiento — solicitudes y respuestas
# ============================================================================

class JobDiscoveryRunRequest(BaseModel):
    query: Optional[str] = Field(None, max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    providers: Optional[List[str]] = None
    target_role_id: Optional[str] = None
    include_company_boards: bool = False
    remote: bool = False


class JobDiscoveryRunResponse(BaseModel):
    query: str
    location: Optional[str] = None
    listings: List[JobListingSchema]
    errors: List[ProviderErrorSchema] = []


# ============================================================================
# Importación y guardado — solicitudes y respuestas
# ============================================================================

class ImportUrlRequest(BaseModel):
    url: str = Field(..., min_length=8, max_length=500)


class SaveListingsRequest(BaseModel):
    listings: List[JobListingSchema] = Field(..., min_length=1)
    target_role_id: Optional[str] = None


class SavedVacancySchema(BaseModel):
    id: str
    vacancy_url: str
    company: str
    exact_role: str


class SkippedListingSchema(BaseModel):
    vacancy_url: Optional[str] = None
    reason: str


class SaveListingsResponse(BaseModel):
    created: List[SavedVacancySchema]
    skipped: List[SkippedListingSchema]
