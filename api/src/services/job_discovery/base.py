"""Adapter contract for every job board / facade."""
from typing import Optional, Protocol

from services.job_discovery.types import JobListing, SearchQuery


# ============================================================================
# Contrato del adaptador
# ============================================================================

class JobBoardAdapter(Protocol):
    id: str
    label: str
    listing_kind: str

    def is_enabled(self) -> bool:
        ...

    def disabled_reason(self) -> Optional[str]:
        ...

    async def search(self, query: SearchQuery) -> list[JobListing]:
        ...
