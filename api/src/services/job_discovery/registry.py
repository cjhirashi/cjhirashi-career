"""Market-board adapters exposed as named providers."""
from typing import Dict, List

from services.job_discovery.getonboard import GetOnBoardAdapter
from services.job_discovery.indeed import IndeedAdapter
from services.job_discovery.linkedin import LinkedInSearchAdapter
from services.job_discovery.remoteok import RemoteOKAdapter
from services.job_discovery.remotive import RemotiveAdapter
from services.job_discovery.types import ProviderStatus

# Indeed is the product name; Adzuna is an internal via, not a UI provider.
MARKET_ADAPTERS = (
    GetOnBoardAdapter(),
    IndeedAdapter(),
    LinkedInSearchAdapter(),
    RemotiveAdapter(),
    RemoteOKAdapter(),
)


def adapters_by_id() -> Dict[str, object]:
    return {adapter.id: adapter for adapter in MARKET_ADAPTERS}


def list_provider_statuses() -> List[ProviderStatus]:
    statuses: List[ProviderStatus] = []
    for adapter in MARKET_ADAPTERS:
        statuses.append(
            ProviderStatus(
                id=adapter.id,
                label=adapter.label,
                enabled=adapter.is_enabled(),
                reason=adapter.disabled_reason(),
                listing_kind=adapter.listing_kind,
            )
        )
    statuses.append(
        ProviderStatus(
            id="company_boards",
            label="Boards de empresas diana (Greenhouse / Lever)",
            enabled=True,
            listing_kind="job",
        )
    )
    return statuses
