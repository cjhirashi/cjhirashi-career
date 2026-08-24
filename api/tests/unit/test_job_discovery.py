"""Unit tests for job discovery adapters and orchestration."""
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.job_discovery.adzuna import listings_from_adzuna_payload
from services.job_discovery.getonboard import listings_from_getonboard_payload
from services.job_discovery.greenhouse import listings_from_greenhouse_payload
from services.job_discovery.indeed import IndeedAdapter
from services.job_discovery.lever import listings_from_lever_payload
from services.job_discovery.linkedin import LinkedInSearchAdapter, build_linkedin_search_urls
from services.job_discovery.registry import list_provider_statuses
from services.job_discovery.remoteok import listings_from_remoteok_payload
from services.job_discovery.remotive import listings_from_remotive_payload
from services.job_discovery.preview_store import remember_preview, reset_for_tests, resolve_refs
from services.job_discovery.service import run_discovery, save_listings
from services.job_discovery.types import CompanyBoard, JobListing, SearchQuery
from services.job_discovery.url_import import infer_source, listing_from_html


def test_indeed_disabled_without_keys():
    adapter = IndeedAdapter()
    assert adapter.is_enabled() is False
    assert adapter.disabled_reason()


def test_linkedin_builds_official_search_urls():
    query = SearchQuery(query="Backend", location="Mexico", remote=True)
    urls = build_linkedin_search_urls(query)
    assert urls
    assert all(u.startswith("https://www.linkedin.com/jobs/search/?") for u in urls)
    assert any("keywords=Backend" in u for u in urls)


@pytest.mark.asyncio
async def test_linkedin_adapter_returns_search_urls():
    listings = await LinkedInSearchAdapter().search(SearchQuery(query="SRE", location="Mexico"))
    assert listings
    assert all(item.listing_kind == "search_url" for item in listings)
    assert all(item.source == "linkedin" for item in listings)


def test_adzuna_payload_maps_to_indeed_source():
    payload = {
        "results": [
            {
                "id": "1",
                "title": "Staff Engineer",
                "redirect_url": "https://www.adzuna.com/land/ad/1",
                "created": "2026-08-01T00:00:00Z",
                "company": {"display_name": "Acme"},
                "location": {"display_name": "CDMX"},
                "description": "Python",
            }
        ]
    }
    listings = listings_from_adzuna_payload(payload, source="indeed", via="adzuna", limit=10)
    assert listings[0].source == "indeed"
    assert listings[0].via == "adzuna"
    assert listings[0].company == "Acme"
    assert listings[0].exact_role == "Staff Engineer"


def test_getonboard_payload():
    payload = {
        "data": [
            {
                "id": "python-dev-1",
                "attributes": {"title": "Python Dev", "remote": True, "published_at": 1700000000},
                "relationships": {"company": {"data": {"id": "acme", "type": "company"}}},
                "links": {"public_url": "https://www.getonbrd.com/jobs/python-dev-1"},
            }
        ],
        "included": [{"id": "acme", "type": "company", "attributes": {"name": "Acme Labs"}}],
    }
    listings = listings_from_getonboard_payload(payload, 10)
    assert listings[0].company == "Acme Labs"
    assert listings[0].source == "getonboard"


def test_remotive_and_remoteok_payloads():
    remotive = listings_from_remotive_payload(
        {
            "jobs": [
                {
                    "id": 9,
                    "title": "Remote Python",
                    "url": "https://remotive.com/jobs/9",
                    "company_name": "Remo",
                    "publication_date": "2026-01-01T00:00:00",
                }
            ]
        },
        10,
    )
    assert remotive[0].source == "remotive"
    remoteok = listings_from_remoteok_payload(
        [
            {"legal": "notice"},
            {
                "id": 3,
                "position": "Python Engineer",
                "company": "OK Inc",
                "url": "https://remoteok.com/l/3",
                "tags": ["python"],
            },
        ],
        SearchQuery(query="python"),
    )
    assert remoteok[0].source == "remoteok"


def test_greenhouse_and_lever_filter_by_query():
    board = CompanyBoard(company_name="Stripe", provider="greenhouse", token="stripe")
    query = SearchQuery(query="engineer")
    gh = listings_from_greenhouse_payload(
        {
            "jobs": [
                {"id": 1, "title": "Software Engineer", "absolute_url": "https://boards.greenhouse.io/x/1"},
                {"id": 2, "title": "Accountant", "absolute_url": "https://boards.greenhouse.io/x/2"},
            ]
        },
        board,
        query,
    )
    assert len(gh) == 1
    assert gh[0].source == "greenhouse"
    lever = listings_from_lever_payload(
        [
            {"id": "a", "text": "Backend Engineer", "hostedUrl": "https://jobs.lever.co/x/a"},
            {"id": "b", "text": "Chef", "hostedUrl": "https://jobs.lever.co/x/b"},
        ],
        CompanyBoard(company_name="Notion", provider="lever", token="notion"),
        query,
    )
    assert len(lever) == 1
    assert lever[0].source == "lever"


def test_url_import_infers_source_and_og_title():
    assert infer_source("https://www.linkedin.com/jobs/view/123") == "linkedin"
    assert infer_source("https://mx.indeed.com/viewjob?jk=abc") == "indeed"
    html = """
    <html><head>
      <meta property="og:title" content="Staff SRE - Example | LinkedIn" />
      <meta property="og:site_name" content="LinkedIn" />
    </head></html>
    """
    listing = listing_from_html("https://www.linkedin.com/jobs/view/123", html)
    assert listing.source == "linkedin"
    assert listing.exact_role == "Staff SRE"
    assert listing.company == "Example"


def test_providers_include_indeed_and_linkedin():
    ids = {p.id for p in list_provider_statuses()}
    assert {"indeed", "linkedin", "getonboard", "remotive", "remoteok", "company_boards"} <= ids
    indeed = next(p for p in list_provider_statuses() if p.id == "indeed")
    assert indeed.enabled is False


def _empty_result(rows=None):
    result = MagicMock()
    result.all.return_value = rows or []
    result.scalar_one_or_none.return_value = None
    result.scalars.return_value.all.return_value = []
    return result


def _db_mock(rows=None):
    db = AsyncMock()
    db.execute.return_value = _empty_result(rows)
    return db


@pytest.mark.asyncio
async def test_run_does_not_persist():
    fake = [
        JobListing(
            company="Acme",
            exact_role="Engineer",
            vacancy_url="https://www.getonbrd.com/jobs/1",
            source="getonboard",
        )
    ]
    db = _db_mock()
    with patch(
        "services.job_discovery.getonboard.GetOnBoardAdapter.search",
        new=AsyncMock(return_value=fake),
    ):
        result = await run_discovery(
            db,
            user_id=1,
            query_text="engineer",
            providers=["getonboard"],
        )
    assert result.listings[0].exact_role == "Engineer"
    db.add.assert_not_called()
    db.commit.assert_not_called()


@pytest.mark.asyncio
async def test_save_then_skip_duplicate():
    db = _db_mock()
    listing = {
        "company": "Acme",
        "exact_role": "Engineer",
        "vacancy_url": "https://example.com/job/1",
        "source": "getonboard",
        "listing_kind": "job",
    }
    first = await save_listings(db, user_id=1, listings=[listing])
    assert len(first["created"]) == 1
    db.execute.return_value = _empty_result([("https://example.com/job/1",)])
    second = await save_listings(db, user_id=1, listings=[listing])
    assert second["created"] == []
    assert second["skipped"][0]["reason"] == "already_saved"


@pytest.mark.asyncio
async def test_save_skips_linkedin_search_urls():
    db = _db_mock()
    result = await save_listings(
        db,
        user_id=1,
        listings=[
            {
                "company": "LinkedIn",
                "exact_role": "Búsqueda: SRE",
                "vacancy_url": "https://www.linkedin.com/jobs/search/?keywords=SRE",
                "source": "linkedin",
                "listing_kind": "search_url",
            }
        ],
    )
    assert result["created"] == []
    assert result["skipped"][0]["reason"] == "search_url"
    db.add.assert_not_called()


@pytest.mark.asyncio
async def test_failed_adapter_does_not_abort():
    db = _db_mock()
    with patch(
        "services.job_discovery.getonboard.GetOnBoardAdapter.search",
        new=AsyncMock(side_effect=RuntimeError("down")),
    ), patch(
        "services.job_discovery.linkedin.LinkedInSearchAdapter.search",
        new=AsyncMock(
            return_value=[
                JobListing(
                    company="LinkedIn",
                    exact_role="Búsqueda",
                    vacancy_url="https://www.linkedin.com/jobs/search/?keywords=x",
                    source="linkedin",
                    listing_kind="search_url",
                )
            ]
        ),
    ):
        result = await run_discovery(
            db,
            user_id=1,
            query_text="x",
            providers=["getonboard", "linkedin"],
        )
    assert result.listings
    assert any(e.provider == "getonboard" for e in result.errors)


def test_found_date_type():
    assert isinstance(date.today(), date)


@pytest.fixture(autouse=True)
def _reset_preview_store():
    reset_for_tests()
    yield
    reset_for_tests()


def test_preview_refs_roundtrip():
    remembered = remember_preview(
        1,
        "sess",
        [
            {
                "company": "Acme",
                "exact_role": "Engineer",
                "vacancy_url": "https://example.com/job/1",
                "source": "getonboard",
                "listing_kind": "job",
            }
        ],
    )
    assert remembered[0]["ref"] == "L1"
    found, missing, available = resolve_refs(1, "sess", ["l1"])
    assert missing == []
    assert available == ["L1"]
    assert found[0]["company"] == "Acme"


@pytest.mark.asyncio
async def test_run_assigns_refs_without_persisting():
    fake = [
        JobListing(
            company="Acme",
            exact_role="Engineer",
            vacancy_url="https://www.getonbrd.com/jobs/1",
            source="getonboard",
        )
    ]
    db = _db_mock()
    with patch(
        "services.job_discovery.getonboard.GetOnBoardAdapter.search",
        new=AsyncMock(return_value=fake),
    ):
        result = await run_discovery(
            db,
            user_id=1,
            query_text="engineer",
            providers=["getonboard"],
            session_key="chat-1",
        )
    assert result.listings[0].ref == "L1"
    db.add.assert_not_called()


@pytest.mark.asyncio
async def test_save_tool_rejects_invented_listings_without_refs():
    from services.bedrock.tools import execute_tool

    db = _db_mock()
    result = await execute_tool(
        db,
        1,
        "save_job_listings",
        {
            "listings": [
                {
                    "company": "Fake",
                    "exact_role": "Invented",
                    "vacancy_url": "https://example.com/invented",
                    "source": "indeed",
                    "listing_kind": "job",
                }
            ]
        },
        "chat-1",
    )
    assert result.get("error")
    db.add.assert_not_called()


@pytest.mark.asyncio
async def test_save_tool_creates_authorized_refs():
    from services.bedrock.tools import execute_tool

    remember_preview(
        1,
        "chat-1",
        [
            {
                "company": "Acme",
                "exact_role": "Engineer",
                "vacancy_url": "https://example.com/job/authorized",
                "source": "getonboard",
                "listing_kind": "job",
            }
        ],
    )
    db = _db_mock()
    result = await execute_tool(db, 1, "save_job_listings", {"refs": ["L1"]}, "chat-1")
    assert len(result["created"]) == 1
    assert result["created"][0]["company"] == "Acme"
    db.add.assert_called()
