"""Shared DTOs for job-board adapters."""
from dataclasses import dataclass, field
from datetime import date
from typing import List, Literal, Optional


ListingKind = Literal["job", "search_url"]


# ============================================================================
# Modelos de datos
# ============================================================================

@dataclass
class CompanyBoard:
    """A target company with a public Greenhouse or Lever board."""

    company_name: str
    provider: Literal["greenhouse", "lever"]
    token: str


@dataclass
class SearchQuery:
    query: str
    location: Optional[str] = None
    remote: bool = False
    limit: int = 20
    company_boards: List[CompanyBoard] = field(default_factory=list)


@dataclass
class JobListing:
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


@dataclass
class ProviderStatus:
    id: str
    label: str
    enabled: bool
    reason: Optional[str] = None
    listing_kind: ListingKind = "job"


@dataclass
class ProviderError:
    provider: str
    message: str


@dataclass
class DiscoveryResult:
    listings: List[JobListing]
    errors: List[ProviderError]
    query: str
    location: Optional[str] = None
