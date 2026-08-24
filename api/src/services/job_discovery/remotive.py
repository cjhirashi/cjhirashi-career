"""Remotive public remote-jobs API."""
from datetime import date, datetime
from typing import Any, Optional

from services.job_discovery.http import get_json
from services.job_discovery.types import JobListing, SearchQuery

SEARCH_URL = "https://remotive.com/api/remote-jobs"


def _parse_date(raw: Optional[str]) -> Optional[date]:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def listings_from_remotive_payload(payload: Any, limit: int) -> list[JobListing]:
    jobs = payload.get("jobs") if isinstance(payload, dict) else None
    if not isinstance(jobs, list):
        return []
    listings: list[JobListing] = []
    for item in jobs[:limit]:
        if not isinstance(item, dict):
            continue
        title = item.get("title") or ""
        url = item.get("url") or ""
        if not title or not url:
            continue
        listings.append(
            JobListing(
                company=str(item.get("company_name") or "Unknown")[:255],
                exact_role=str(title)[:255],
                vacancy_url=str(url)[:500],
                source="remotive",
                found_date=_parse_date(item.get("publication_date")),
                location=item.get("candidate_required_location"),
                salary_text=item.get("salary") or None,
                remote=True,
                snippet=None,
                external_id=str(item.get("id")) if item.get("id") is not None else None,
            )
        )
    return listings


class RemotiveAdapter:
    id = "remotive"
    label = "Remotive"
    listing_kind = "job"

    def is_enabled(self) -> bool:
        return True

    def disabled_reason(self) -> Optional[str]:
        return None

    async def search(self, query: SearchQuery) -> list[JobListing]:
        payload = await get_json(
            SEARCH_URL,
            params={"search": query.query, "limit": min(query.limit, 50)},
        )
        return listings_from_remotive_payload(payload, query.limit)
