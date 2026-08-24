"""Greenhouse public job-board API for a single company token."""
from datetime import date, datetime
from typing import Any, Optional

from services.job_discovery.http import get_json
from services.job_discovery.types import CompanyBoard, JobListing, SearchQuery


def _parse_date(raw: Optional[str]) -> Optional[date]:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def listings_from_greenhouse_payload(
    payload: Any,
    board: CompanyBoard,
    query: SearchQuery,
) -> list[JobListing]:
    jobs = payload.get("jobs") if isinstance(payload, dict) else None
    if not isinstance(jobs, list):
        return []
    needle = query.query.lower()
    listings: list[JobListing] = []
    for item in jobs:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "")
        url = str(item.get("absolute_url") or "")
        if not title or not url:
            continue
        if needle and needle not in title.lower():
            continue
        loc = None
        if isinstance(item.get("location"), dict):
            loc = item["location"].get("name")
        listings.append(
            JobListing(
                company=board.company_name[:255],
                exact_role=title[:255],
                vacancy_url=url[:500],
                source="greenhouse",
                found_date=_parse_date(item.get("updated_at") or item.get("first_published")),
                location=loc,
                remote=None,
                snippet=None,
                external_id=str(item.get("id")) if item.get("id") is not None else None,
            )
        )
        if len(listings) >= query.limit:
            break
    return listings


async def search_greenhouse_board(board: CompanyBoard, query: SearchQuery) -> list[JobListing]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{board.token}/jobs"
    payload = await get_json(url)
    return listings_from_greenhouse_payload(payload, board, query)
