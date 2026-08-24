"""RemoteOK public JSON feed. Requires a real User-Agent (set in http.py)."""
from datetime import date, datetime
from typing import Any, Optional

from services.job_discovery.http import get_json
from services.job_discovery.types import JobListing, SearchQuery

FEED_URL = "https://remoteok.com/api"


def _parse_date(item: dict[str, Any]) -> Optional[date]:
    raw = item.get("date") or item.get("epoch")
    if isinstance(raw, (int, float)):
        return datetime.utcfromtimestamp(int(raw)).date()
    if isinstance(raw, str):
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00")).date()
        except ValueError:
            return None
    return None


def listings_from_remoteok_payload(payload: Any, query: SearchQuery) -> list[JobListing]:
    if not isinstance(payload, list):
        return []
    needle = query.query.lower()
    listings: list[JobListing] = []
    for item in payload:
        if not isinstance(item, dict) or "id" not in item:
            continue
        title = str(item.get("position") or item.get("title") or "")
        company = str(item.get("company") or "Unknown")
        haystack = " ".join(
            [
                title,
                company,
                str(item.get("description") or ""),
                " ".join(item.get("tags") or []),
            ]
        ).lower()
        if needle and needle not in haystack:
            continue
        url = str(item.get("url") or item.get("apply_url") or "")
        if not title or not url:
            continue
        listings.append(
            JobListing(
                company=company[:255],
                exact_role=title[:255],
                vacancy_url=url[:500],
                source="remoteok",
                found_date=_parse_date(item),
                location=item.get("location"),
                salary_text=str(item["salary"]) if item.get("salary") else None,
                remote=True,
                snippet=None,
                external_id=str(item.get("id")),
            )
        )
        if len(listings) >= query.limit:
            break
    return listings


class RemoteOKAdapter:
    id = "remoteok"
    label = "RemoteOK"
    listing_kind = "job"

    def is_enabled(self) -> bool:
        return True

    def disabled_reason(self) -> Optional[str]:
        return None

    async def search(self, query: SearchQuery) -> list[JobListing]:
        payload = await get_json(FEED_URL)
        return listings_from_remoteok_payload(payload, query)
