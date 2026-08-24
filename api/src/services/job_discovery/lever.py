"""Lever public postings API for a single company site slug."""
from datetime import date, datetime
from typing import Any, Optional

from services.job_discovery.http import get_json
from services.job_discovery.types import CompanyBoard, JobListing, SearchQuery


def _parse_date(raw: Any) -> Optional[date]:
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        # Lever uses milliseconds.
        ts = int(raw) / 1000 if raw > 10_000_000_000 else int(raw)
        return datetime.utcfromtimestamp(ts).date()
    if isinstance(raw, str):
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00")).date()
        except ValueError:
            return None
    return None


def listings_from_lever_payload(
    payload: Any,
    board: CompanyBoard,
    query: SearchQuery,
) -> list[JobListing]:
    jobs = payload if isinstance(payload, list) else []
    needle = query.query.lower()
    listings: list[JobListing] = []
    for item in jobs:
        if not isinstance(item, dict):
            continue
        title = str(item.get("text") or item.get("title") or "")
        url = str(item.get("hostedUrl") or item.get("applyUrl") or "")
        if not title or not url:
            continue
        if needle and needle not in title.lower():
            continue
        cats = item.get("categories") or {}
        loc = None
        if isinstance(cats, dict):
            loc = cats.get("location")
        listings.append(
            JobListing(
                company=board.company_name[:255],
                exact_role=title[:255],
                vacancy_url=url[:500],
                source="lever",
                found_date=_parse_date(item.get("createdAt")),
                location=loc,
                remote=(item.get("workplaceType") or "").lower() == "remote" or None,
                snippet=None,
                external_id=str(item.get("id")) if item.get("id") is not None else None,
            )
        )
        if len(listings) >= query.limit:
            break
    return listings


async def search_lever_board(board: CompanyBoard, query: SearchQuery) -> list[JobListing]:
    url = f"https://api.lever.co/v0/postings/{board.token}"
    payload = await get_json(url, params={"mode": "json"})
    return listings_from_lever_payload(payload, board, query)
