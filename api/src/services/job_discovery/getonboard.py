"""Get on Board public search API (LATAM tech)."""
from datetime import date, datetime
from typing import Any, Optional
from urllib.parse import quote

from services.job_discovery.http import get_json
from services.job_discovery.types import JobListing, SearchQuery

SEARCH_URL = "https://www.getonbrd.com/api/v0/search/jobs"


def _company_name(item: dict[str, Any], included: list[dict[str, Any]]) -> str:
    attrs = item.get("attributes") or {}
    if attrs.get("company_name"):
        return str(attrs["company_name"])
    rel = ((item.get("relationships") or {}).get("company") or {}).get("data") or {}
    company_id = rel.get("id")
    if company_id:
        for row in included:
            if row.get("id") == company_id and row.get("type") == "company":
                name = (row.get("attributes") or {}).get("name")
                if name:
                    return str(name)
    return "Unknown"


def _public_url(item: dict[str, Any]) -> str:
    links = item.get("links") or {}
    if links.get("public_url"):
        return str(links["public_url"])
    job_id = item.get("id") or ""
    return f"https://www.getonbrd.com/jobs/{job_id}"


def _found_date(attrs: dict[str, Any]) -> Optional[date]:
    raw = attrs.get("published_at")
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return datetime.utcfromtimestamp(int(raw)).date()
    if isinstance(raw, str):
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00")).date()
        except ValueError:
            return None
    return None


def listings_from_getonboard_payload(payload: Any, limit: int) -> list[JobListing]:
    data = payload.get("data") if isinstance(payload, dict) else None
    included = payload.get("included") if isinstance(payload, dict) else []
    if not isinstance(data, list):
        return []
    if not isinstance(included, list):
        included = []
    listings: list[JobListing] = []
    for item in data[:limit]:
        if not isinstance(item, dict):
            continue
        attrs = item.get("attributes") or {}
        title = attrs.get("title") or ""
        url = _public_url(item)
        if not title:
            continue
        min_s = attrs.get("min_salary")
        max_s = attrs.get("max_salary")
        salary = None
        if min_s and max_s:
            salary = f"{min_s}-{max_s} {attrs.get('currency') or ''}".strip()
        listings.append(
            JobListing(
                company=_company_name(item, included)[:255],
                exact_role=str(title)[:255],
                vacancy_url=url[:500],
                source="getonboard",
                found_date=_found_date(attrs),
                location=attrs.get("country") or attrs.get("cities"),
                salary_text=salary,
                remote=bool(attrs.get("remote")) if attrs.get("remote") is not None else None,
                snippet=(attrs.get("description_headline") or "")[:400] or None,
                external_id=str(item.get("id")) if item.get("id") is not None else None,
            )
        )
    return listings


class GetOnBoardAdapter:
    id = "getonboard"
    label = "Get on Board"
    listing_kind = "job"

    def is_enabled(self) -> bool:
        return True

    def disabled_reason(self) -> Optional[str]:
        return None

    async def search(self, query: SearchQuery) -> list[JobListing]:
        payload = await get_json(
            SEARCH_URL,
            params={"query": query.query, "per_page": min(query.limit, 25)},
        )
        return listings_from_getonboard_payload(payload, query.limit)


def search_url_for(query: str) -> str:
    return f"https://www.getonbrd.com/jobs?q={quote(query)}"
