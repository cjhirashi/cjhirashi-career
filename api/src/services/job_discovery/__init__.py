"""Job discovery adapters and orchestration."""

# ============================================================================
# Reexportaciones públicas
# ============================================================================

from services.job_discovery.service import (
    import_vacancy_url,
    listing_to_dict,
    providers,
    run_discovery,
    save_listings,
)

__all__ = [
    "import_vacancy_url",
    "listing_to_dict",
    "providers",
    "run_discovery",
    "save_listings",
]
