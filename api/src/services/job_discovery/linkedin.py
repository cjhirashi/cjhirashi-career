"""LinkedIn logical provider — official search URLs only, no scrape."""
from typing import Optional
from urllib.parse import urlencode

from services.job_discovery.types import JobListing, SearchQuery


# ============================================================================
# Construcción de URLs de búsqueda
# ============================================================================

def build_linkedin_search_urls(query: SearchQuery) -> list[str]:
    location = query.location or "Mexico"
    urls = [
        "https://www.linkedin.com/jobs/search/?"
        + urlencode({"keywords": query.query, "location": location}),
        "https://www.linkedin.com/jobs/search/?"
        + urlencode({"keywords": query.query, "location": location, "f_TPR": "r604800"}),
    ]
    if query.remote or (query.location and "remote" in query.location.lower()):
        urls.insert(
            1,
            "https://www.linkedin.com/jobs/search/?"
            + urlencode({"keywords": query.query, "location": location, "f_WT": "2"}),
        )
    # Deduplicate while keeping order.
    seen: set[str] = set()
    unique: list[str] = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            unique.append(url)
    return unique[:3]


# ============================================================================
# Adaptador LinkedIn
# ============================================================================

class LinkedInSearchAdapter:
    id = "linkedin"
    label = "LinkedIn"
    listing_kind = "search_url"

    def is_enabled(self) -> bool:
        return True

    def disabled_reason(self) -> Optional[str]:
        return None

    async def search(self, query: SearchQuery) -> list[JobListing]:
        location = query.location or "Mexico"
        listings: list[JobListing] = []
        labels = ["Búsqueda actual", "Última semana", "Remoto"]
        for i, url in enumerate(build_linkedin_search_urls(query)):
            label = labels[i] if i < len(labels) else f"Búsqueda {i + 1}"
            listings.append(
                JobListing(
                    company="LinkedIn",
                    exact_role=f"{label}: {query.query}",
                    vacancy_url=url,
                    source="linkedin",
                    listing_kind="search_url",
                    location=location,
                    snippet="Abre esta búsqueda oficial en LinkedIn e importa cada vacante con su URL jobs/view.",
                )
            )
        return listings
