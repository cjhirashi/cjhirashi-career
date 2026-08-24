"""Adzuna official job-search API. Used as the Indeed backend."""
from datetime import date, datetime
from typing import Any, Optional

from config import settings
from services.job_discovery.http import get_json
from services.job_discovery.types import JobListing, SearchQuery


# ============================================================================
# Configuración y parseo
# ============================================================================

def adzuna_configured() -> bool:
    return bool(settings.ADZUNA_APP_ID and settings.ADZUNA_APP_KEY)


def _parse_date(raw: Optional[str]) -> Optional[date]:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def _salary(item: dict[str, Any]) -> Optional[str]:
    low = item.get("salary_min")
    high = item.get("salary_max")
    if low and high:
        return f"{int(low)}-{int(high)}"
    if low:
        return str(int(low))
    if high:
        return str(int(high))
    return None


def listings_from_adzuna_payload(
    payload: Any,
    *,
    source: str,
    via: str = "adzuna",
    limit: int,
) -> list[JobListing]:
    results = payload.get("results") if isinstance(payload, dict) else None
    if not isinstance(results, list):
        return []
    listings: list[JobListing] = []
    for item in results[:limit]:
        if not isinstance(item, dict):
            continue
        company = (item.get("company") or {}).get("display_name") or "Unknown"
        title = item.get("title") or ""
        url = item.get("redirect_url") or item.get("adref") or ""
        if not title or not url:
            continue
        listings.append(
            JobListing(
                company=str(company)[:255],
                exact_role=str(title)[:255],
                vacancy_url=str(url)[:500],
                source=source,
                via=via,
                found_date=_parse_date(item.get("created")),
                location=(item.get("location") or {}).get("display_name"),
                salary_text=_salary(item),
                snippet=(item.get("description") or "")[:400] or None,
                external_id=str(item.get("id")) if item.get("id") is not None else None,
            )
        )
    return listings


# ============================================================================
# Búsqueda
# ============================================================================

async def search_adzuna(query: SearchQuery) -> list[JobListing]:
    if not adzuna_configured():
        raise RuntimeError("Adzuna is not configured")
    country = settings.ADZUNA_COUNTRY or "mx"
    url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
    params: dict[str, Any] = {
        "app_id": settings.ADZUNA_APP_ID,
        "app_key": settings.ADZUNA_APP_KEY,
        "what": query.query,
        "results_per_page": min(query.limit, 50),
        "content-type": "application/json",
    }
    if query.location:
        params["where"] = query.location
    payload = await get_json(url, params=params)
    return listings_from_adzuna_payload(payload, source="indeed", via="adzuna", limit=query.limit)
