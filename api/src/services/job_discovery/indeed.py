"""Indeed logical provider — Adzuna-backed, never calls Indeed.com."""
from typing import Optional

from services.job_discovery.adzuna import adzuna_configured, search_adzuna
from services.job_discovery.types import JobListing, SearchQuery


# ============================================================================
# Adaptador Indeed
# ============================================================================

class IndeedAdapter:
    id = "indeed"
    label = "Indeed"
    listing_kind = "job"

    def is_enabled(self) -> bool:
        return adzuna_configured()

    def disabled_reason(self) -> Optional[str]:
        if self.is_enabled():
            return None
        return "Faltan ADZUNA_APP_ID y ADZUNA_APP_KEY"

    async def search(self, query: SearchQuery) -> list[JobListing]:
        return await search_adzuna(query)
