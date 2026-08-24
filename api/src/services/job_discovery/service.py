"""Orchestrates adapters, URL import, and vacancy persistence."""
import asyncio
import logging
from datetime import date
from typing import Iterable, List, Optional, Sequence

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models.target_company import TargetCompany
from models.target_role import TargetRole
from models.vacancy import Vacancy
from services.job_discovery.greenhouse import search_greenhouse_board
from services.job_discovery.lever import search_lever_board
from services.job_discovery.registry import adapters_by_id, list_provider_statuses
from services.job_discovery.types import (
    CompanyBoard,
    DiscoveryResult,
    JobListing,
    ProviderError,
    SearchQuery,
)
from services.job_discovery.preview_store import remember_preview
from services.job_discovery.url_import import import_url as import_vacancy_url

logger = logging.getLogger(__name__)

DEFAULT_PROVIDERS = ("getonboard", "indeed", "linkedin", "remotive", "remoteok")


def _analysis_notes(raw: dict) -> Optional[str]:
    parts: list[str] = []
    snippet = (raw.get("snippet") or "").strip()
    if snippet:
        parts.append(snippet)
    extras: list[str] = []
    if raw.get("location"):
        extras.append(f"Ubicación: {raw['location']}")
    if raw.get("salary_text"):
        extras.append(f"Salario: {raw['salary_text']}")
    if raw.get("via"):
        extras.append(f"Vía: {raw['via']}")
    if extras:
        parts.append(" · ".join(extras))
    return "\n".join(parts) or None


def listing_to_dict(listing: JobListing) -> dict:
    return {
        "company": listing.company,
        "exact_role": listing.exact_role,
        "vacancy_url": listing.vacancy_url,
        "source": listing.source,
        "listing_kind": listing.listing_kind,
        "via": listing.via,
        "found_date": listing.found_date.isoformat() if listing.found_date else None,
        "location": listing.location,
        "salary_text": listing.salary_text,
        "remote": listing.remote,
        "snippet": listing.snippet,
        "external_id": listing.external_id,
        "already_saved": listing.already_saved,
        "ref": listing.ref,
    }


async def _saved_urls(db: AsyncSession, user_id: str) -> set[str]:
    result = await db.execute(select(Vacancy.vacancy_url).where(Vacancy.user_id == user_id))
    return {row[0] for row in result.all() if row[0]}


async def _resolve_query(
    db: AsyncSession,
    user_id: str,
    query_text: Optional[str],
    target_role_id: Optional[str],
) -> str:
    if query_text and query_text.strip():
        return query_text.strip()
    if target_role_id is not None:
        result = await db.execute(
            select(TargetRole).where(TargetRole.id == target_role_id, TargetRole.user_id == user_id)
        )
        role = result.scalar_one_or_none()
        if role and role.role_name:
            return role.role_name
    result = await db.execute(
        select(TargetRole)
        .where(TargetRole.user_id == user_id, TargetRole.is_active.is_(True))
        .order_by(TargetRole.priority_order.asc())
        .limit(1)
    )
    role = result.scalar_one_or_none()
    if role and role.role_name:
        return role.role_name
    raise ValueError("Indica un texto de búsqueda o un target_role_id")


async def _load_company_boards(db: AsyncSession, user_id: str) -> List[CompanyBoard]:
    result = await db.execute(
        select(TargetCompany).where(
            TargetCompany.user_id == user_id,
            TargetCompany.career_board_provider.is_not(None),
            TargetCompany.career_board_token.is_not(None),
        )
    )
    boards: List[CompanyBoard] = []
    for row in result.scalars().all():
        provider = (row.career_board_provider or "").lower()
        token = (row.career_board_token or "").strip()
        if provider in ("greenhouse", "lever") and token:
            boards.append(CompanyBoard(company_name=row.company_name, provider=provider, token=token))
    return boards


async def _search_one(adapter, query: SearchQuery) -> list[JobListing]:
    return await adapter.search(query)


async def run_discovery(
    db: AsyncSession,
    user_id: str,
    *,
    query_text: Optional[str] = None,
    location: Optional[str] = None,
    providers: Optional[Sequence[str]] = None,
    target_role_id: Optional[str] = None,
    include_company_boards: bool = False,
    remote: bool = False,
    session_key: Optional[str] = None,
) -> DiscoveryResult:
    query_str = await _resolve_query(db, user_id, query_text, target_role_id)
    wanted = list(providers) if providers else list(DEFAULT_PROVIDERS)
    include_boards = include_company_boards or "company_boards" in wanted
    wanted = [p for p in wanted if p != "company_boards"]

    registry = adapters_by_id()
    query = SearchQuery(
        query=query_str,
        location=location,
        remote=remote,
        limit=20,
    )
    errors: List[ProviderError] = []
    tasks = []
    names: List[str] = []
    for provider_id in wanted:
        adapter = registry.get(provider_id)
        if adapter is None:
            errors.append(ProviderError(provider=provider_id, message="Provider desconocido"))
            continue
        if not adapter.is_enabled():
            errors.append(
                ProviderError(provider=provider_id, message=adapter.disabled_reason() or "Deshabilitado")
            )
            continue
        names.append(provider_id)
        tasks.append(_search_one(adapter, query))

    if include_boards:
        boards = await _load_company_boards(db, user_id)
        query.company_boards = boards
        for board in boards:
            names.append(f"{board.provider}:{board.token}")
            if board.provider == "greenhouse":
                tasks.append(search_greenhouse_board(board, query))
            else:
                tasks.append(search_lever_board(board, query))

    listings: List[JobListing] = []
    if tasks:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for name, result in zip(names, results):
            if isinstance(result, Exception):
                logger.warning("job discovery provider %s failed: %s", name, result)
                errors.append(ProviderError(provider=name, message=str(result)))
                continue
            listings.extend(result)

    saved = await _saved_urls(db, user_id)
    seen_urls: set[str] = set()
    unique: List[JobListing] = []
    for listing in listings:
        url = listing.vacancy_url
        if url in seen_urls:
            continue
        seen_urls.add(url)
        listing.already_saved = url in saved
        unique.append(listing)

    max_results = settings.JOB_DISCOVERY_MAX_RESULTS
    trimmed = unique[:max_results]
    preview = remember_preview(user_id, session_key or "admin", [listing_to_dict(item) for item in trimmed])
    for listing, payload in zip(trimmed, preview):
        listing.ref = payload["ref"]
    return DiscoveryResult(
        listings=trimmed,
        errors=errors,
        query=query_str,
        location=location,
    )


async def save_listings(
    db: AsyncSession,
    user_id: str,
    listings: Iterable[dict],
    *,
    target_role_id: Optional[str] = None,
) -> dict:
    saved_urls = await _saved_urls(db, user_id)
    created: List[dict] = []
    skipped: List[dict] = []
    today = date.today()
    pending: list[Vacancy] = []
    sources_seen: list[str] = []

    for raw in listings:
        kind = raw.get("listing_kind") or "job"
        url = (raw.get("vacancy_url") or "").strip()
        if kind == "search_url":
            skipped.append({"vacancy_url": url, "reason": "search_url"})
            continue
        company = (raw.get("company") or "").strip()
        role = (raw.get("exact_role") or "").strip()
        if not company or not role or not url:
            skipped.append({"vacancy_url": url, "reason": "incomplete"})
            continue
        if url in saved_urls:
            skipped.append({"vacancy_url": url, "reason": "already_saved"})
            continue
        vacancy = Vacancy(
            user_id=user_id,
            company=company[:255],
            exact_role=role[:255],
            vacancy_url=url[:500],
            source=(raw.get("source") or None),
            found_date=today,
            evaluation="pending_review",
            is_active=True,
            analysis_notes=_analysis_notes(raw),
        )
        db.add(vacancy)
        pending.append(vacancy)
        saved_urls.add(url)
        src = raw.get("source")
        if src and src not in sources_seen:
            sources_seen.append(src)

    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        return {
            "created": [],
            "skipped": skipped + [{"vacancy_url": v.vacancy_url, "reason": "already_saved"} for v in pending],
        }

    for vacancy in pending:
        created.append(
            {
                "id": vacancy.id,
                "vacancy_url": vacancy.vacancy_url,
                "company": vacancy.company,
                "exact_role": vacancy.exact_role,
            }
        )

    if target_role_id is not None and created:
        result = await db.execute(
            select(TargetRole).where(TargetRole.id == target_role_id, TargetRole.user_id == user_id)
        )
        role_row = result.scalar_one_or_none()
        if role_row:
            role_row.market_active_vacancies = (role_row.market_active_vacancies or 0) + len(created)
            role_row.market_validated_at = today
            existing = list(role_row.market_sources or [])
            for src in sources_seen:
                if src not in existing:
                    existing.append(src)
            role_row.market_sources = existing

    await db.commit()
    return {"created": created, "skipped": skipped}


def providers() -> list:
    return list_provider_statuses()


__all__ = [
    "import_vacancy_url",
    "listing_to_dict",
    "providers",
    "run_discovery",
    "save_listings",
]
