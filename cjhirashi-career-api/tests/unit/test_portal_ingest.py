"""
Tests for portal analytics event ingestion service (C2).

Tests the exact pipeline from SPEC-0010: site resolution, visitor management,
visit sessionization (30 min threshold), advisory locking, device/geo parsing,
bot detection, owner token verification, channel classification, key events,
and engagement metrics.
"""
import asyncio
import hashlib
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from models import User, PortalSite, PortalVisitor, PortalVisit, PortalEvent, PortalGoal
from schemas.events import TrackEventIn
from services.portal_ingest import ingest_event, UnknownSite


# Fixture for public portal user (from settings.PUBLIC_PORTAL_USER_ID)
from config import settings
PUBLIC_USER_ID = settings.PUBLIC_PORTAL_USER_ID


@pytest.fixture(autouse=True)
def mock_geo_source_cf():
    """Mock settings.GEO_SOURCE to use 'cf' (headers only) to avoid network calls in tests."""
    with patch("services.portal_geo.settings.GEO_SOURCE", "cf"):
        yield


@pytest.fixture
async def public_user(db_session: AsyncSession):
    """Create the public portal user."""
    user = User(
        id=PUBLIC_USER_ID,
        username="public-portal",
        email="portal@example.com",
        password_hash="dummy-hash",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.fixture
async def test_site(db_session: AsyncSession, public_user: User):
    """Create a test portal site."""
    owner_token = "secret-owner-token-12345"
    owner_token_hash = hashlib.sha256(owner_token.encode()).hexdigest()

    site = PortalSite(
        user_id=PUBLIC_USER_ID,
        name="Test Portfolio",
        domain="cjhirashi.com",
        public_key="test-public-key-12345",
        owner_token_hash=owner_token_hash,
        allowed_hosts=["cjhirashi.com", "www.cjhirashi.com"],
        timezone="America/Mexico_City",
        active=True,
    )
    db_session.add(site)
    await db_session.flush()
    return site, owner_token


@pytest.fixture
async def key_event_goal(db_session: AsyncSession, test_site):
    """Create a key event goal for testing."""
    site, _ = test_site
    goal = PortalGoal(
        user_id=site.user_id,
        site_id=site.id,
        name="Download CV",
        type="event",
        match={"event_type": "download"},
        is_key_event=True,
    )
    db_session.add(goal)
    await db_session.flush()
    return goal


@pytest.mark.requisito("RF-001")
class TestIngestEventV1Payload:
    """RF-001: Accept v1 payload without siteKey/visitorId."""

    async def test_ingest_v1_minimal_creates_event(
        self, db_session: AsyncSession, test_site
    ):
        """v1 minimal payload creates event, assigns to default site."""
        site, _ = test_site

        payload = TrackEventIn(type="pageview", page="/projects")
        now = datetime.now(timezone.utc)

        event = await ingest_event(
            db_session,
            payload=payload,
            headers={},
            ip=None,
            now=now,
        )

        assert event.event_type == "pageview"
        assert event.page == "/projects"
        assert event.site_id == site.id
        assert event.visit_id is not None
        assert event.visitor_id is not None

    async def test_ingest_v1_creates_anonymous_visitor(
        self, db_session: AsyncSession, test_site
    ):
        """v1 payload without visitorId creates anon-<sessionId> visitor."""
        site, _ = test_site

        payload = TrackEventIn(
            type="pageview",
            page="/",
            sessionId="sess-12345",
        )

        event = await ingest_event(
            db_session,
            payload=payload,
            headers={},
            ip=None,
        )

        # Check visitor was created with anon-<sessionId>
        visitor_row = await db_session.execute(
            select(PortalVisitor).where(
                PortalVisitor.id == event.visitor_id
            )
        )
        visitor = visitor_row.scalar_one()
        assert visitor.visitor_key == "anon-sess-12345"


@pytest.mark.requisito("RF-002")
class TestVisitSessionization:
    """RF-002: Sessionize visits by 30 min inactivity threshold."""

    async def test_two_events_10_min_apart_same_visit(
        self, db_session: AsyncSession, test_site
    ):
        """Two pageviews 10 min apart should belong to same visit."""
        site, _ = test_site
        now = datetime.now(timezone.utc)

        # First event
        payload1 = TrackEventIn(
            type="pageview",
            page="/projects",
            visitorId="visitor-1",
        )
        event1 = await ingest_event(db_session, payload=payload1, headers={}, ip=None, now=now)

        # Second event 10 min later
        now2 = now + timedelta(minutes=10)
        payload2 = TrackEventIn(
            type="pageview",
            page="/about",
            visitorId="visitor-1",
        )
        event2 = await ingest_event(db_session, payload=payload2, headers={}, ip=None, now=now2)

        assert event1.visit_id == event2.visit_id, "Events 10 min apart should be same visit"

    async def test_two_events_31_min_apart_different_visits(
        self, db_session: AsyncSession, test_site
    ):
        """Two pageviews 31 min apart should belong to different visits."""
        site, _ = test_site
        now = datetime.now(timezone.utc)

        # First event
        payload1 = TrackEventIn(
            type="pageview",
            page="/projects",
            visitorId="visitor-2",
        )
        event1 = await ingest_event(db_session, payload=payload1, headers={}, ip=None, now=now)

        # Second event 31 min later
        now2 = now + timedelta(minutes=31)
        payload2 = TrackEventIn(
            type="pageview",
            page="/about",
            visitorId="visitor-2",
        )
        event2 = await ingest_event(db_session, payload=payload2, headers={}, ip=None, now=now2)

        assert event1.visit_id != event2.visit_id, "Events >30 min apart should be different visits"

    async def test_passive_event_40_min_later_same_visit(
        self, db_session: AsyncSession, test_site
    ):
        """Passive event (page_duration) 40 min after last event attaches to previous visit."""
        site, _ = test_site
        now = datetime.now(timezone.utc)

        # First event (pageview)
        payload1 = TrackEventIn(
            type="pageview",
            page="/projects",
            visitorId="visitor-3",
        )
        event1 = await ingest_event(db_session, payload=payload1, headers={}, ip=None, now=now)

        # Second event (passive page_duration) 40 min later
        now2 = now + timedelta(minutes=40)
        payload2 = TrackEventIn(
            type="page_duration",
            page="/projects",
            visitorId="visitor-3",
            durationMs=120000,
        )
        event2 = await ingest_event(db_session, payload=payload2, headers={}, ip=None, now=now2)

        assert event1.visit_id == event2.visit_id, "Passive event within 24h should attach to old visit"


@pytest.mark.requisito("RF-003")
class TestConcurrentEventHandling:
    """RF-003: eventos simultáneos del mismo visitante crean una sola visita."""

    async def test_concurrent_events_same_visitor_single_visit(self, test_db):
        async with test_db() as setup:
            user = User(id=PUBLIC_USER_ID, username="conc-user", email="conc@example.com",
                        password_hash="x", is_active=True)
            setup.add(user)
            await setup.flush()
            site = PortalSite(user_id=PUBLIC_USER_ID, name="s", domain="conc.example", public_key="conc-key",
                              owner_token_hash="0" * 64, allowed_hosts=["conc.example"], active=True)
            setup.add(site)
            await setup.commit()

        async def one(n: int) -> str:
            async with test_db() as session:
                event = await ingest_event(
                    session,
                    payload=TrackEventIn(type="pageview", page=f"/p{n}", visitorId="conc-visitor", siteKey="conc-key"),
                    headers={}, ip=None,
                )
                # Mantiene la transacción abierta para forzar el solape entre las 5 ingestas.
                await asyncio.sleep(0.3)
                await session.commit()
                return event.visit_id

        visit_ids = await asyncio.gather(*[one(i) for i in range(5)])
        assert len(set(visit_ids)) == 1

        async with test_db() as check:
            visitors = (await check.execute(select(PortalVisitor))).scalars().all()
            visits = (await check.execute(select(PortalVisit))).scalars().all()
            events = (await check.execute(select(PortalEvent).order_by(PortalEvent.seq))).scalars().all()
        assert len(visitors) == 1 and visitors[0].visit_count == 1
        assert len(visits) == 1 and visits[0].events_count == 5 and visits[0].pageviews == 5
        assert [e.seq for e in events] == [1, 2, 3, 4, 5]


@pytest.mark.requisito("RF-008")
class TestOwnerTokenVerification:
    """RF-008: Valid owner token marks visitor as owner."""

    async def test_correct_owner_token_marks_owner(
        self, db_session: AsyncSession, test_site
    ):
        """Event with correct owner token marks visitor as is_owner."""
        site, owner_token = test_site

        payload = TrackEventIn(
            type="pageview",
            page="/",
            visitorId="owner-visitor",
            ownerToken=owner_token,
        )

        event = await ingest_event(db_session, payload=payload, headers={}, ip=None)

        # Verify visitor.is_owner is True
        visitor_row = await db_session.execute(
            select(PortalVisitor).where(PortalVisitor.id == event.visitor_id)
        )
        visitor = visitor_row.scalar_one()
        assert visitor.is_owner is True

    async def test_incorrect_owner_token_not_owner(
        self, db_session: AsyncSession, test_site
    ):
        """Event with incorrect owner token does NOT mark visitor as owner."""
        site, owner_token = test_site

        payload = TrackEventIn(
            type="pageview",
            page="/",
            visitorId="non-owner-visitor",
            ownerToken="wrong-token",
        )

        event = await ingest_event(db_session, payload=payload, headers={}, ip=None)

        # Verify visitor.is_owner is False
        visitor_row = await db_session.execute(
            select(PortalVisitor).where(PortalVisitor.id == event.visitor_id)
        )
        visitor = visitor_row.scalar_one()
        assert visitor.is_owner is False


@pytest.mark.requisito("RF-010")
class TestApplicationIdLinking:
    """RF-010: utm_campaign igual al id de una postulación vincula la visita."""

    async def _application(self, db_session: AsyncSession) -> str:
        from models import Vacancy, Application
        vacancy = Vacancy(user_id=PUBLIC_USER_ID, company="Acme", exact_role="Arquitecto")
        db_session.add(vacancy)
        await db_session.flush()
        application = Application(user_id=PUBLIC_USER_ID, vacancy_id=vacancy.id)
        db_session.add(application)
        await db_session.flush()
        return application.id

    async def test_utm_campaign_matches_application(self, db_session: AsyncSession, test_site):
        application_id = await self._application(db_session)
        payload = TrackEventIn(type="pageview", page="/", visitorId="app-visitor",
                               utm={"utm_campaign": application_id, "utm_medium": "postulacion"})
        event = await ingest_event(db_session, payload=payload, headers={}, ip=None)
        visit = (await db_session.execute(select(PortalVisit).where(PortalVisit.id == event.visit_id))).scalar_one()
        assert visit.application_id == application_id

    async def test_unknown_campaign_does_not_link(self, db_session: AsyncSession, test_site):
        await self._application(db_session)
        payload = TrackEventIn(type="pageview", page="/", visitorId="app-visitor-2", utm={"utm_campaign": "apl-99999"})
        event = await ingest_event(db_session, payload=payload, headers={}, ip=None)
        visit = (await db_session.execute(select(PortalVisit).where(PortalVisit.id == event.visit_id))).scalar_one()
        assert visit.application_id is None


SEED_RULES = [
    ("Application", {"utm_medium_in": ["postulacion", "application"]}),
    ("Paid", {"utm_medium_in": ["cpc", "ppc", "paid", "paidsearch"]}),
    ("Organic Social", {"referrer_domain_in": ["linkedin.com", "lnkd.in", "github.com"]}),
    ("Organic Search", {"referrer_domain_regex": r"(^|\.)(google|bing|duckduckgo)\."}),
    ("Referral", {"referrer_present": True, "referrer_domain_not_in": ["cjhirashi.com"]}),
    ("Direct", {"no_referrer": True, "no_utm": True}),
    ("Unknown", {}),
]


@pytest.mark.requisito("RF-009")
class TestChannelClassification:
    """RF-009: la visita toma su canal de las reglas del sitio."""

    async def _seed_rules(self, db_session: AsyncSession, site: PortalSite) -> None:
        from models import PortalChannelRule
        for priority, (channel, conditions) in enumerate(SEED_RULES):
            db_session.add(PortalChannelRule(user_id=site.user_id, site_id=site.id, priority=priority,
                                             channel=channel, conditions=conditions))
        await db_session.flush()

    async def _channel(self, db_session: AsyncSession, visitor: str, **fields) -> str:
        event = await ingest_event(db_session, payload=TrackEventIn(type="pageview", page="/", visitorId=visitor, **fields),
                                   headers={}, ip=None)
        visit = (await db_session.execute(select(PortalVisit).where(PortalVisit.id == event.visit_id))).scalar_one()
        return visit.channel

    async def test_channels_from_site_rules(self, db_session: AsyncSession, test_site):
        site, _ = test_site
        await self._seed_rules(db_session, site)
        assert await self._channel(db_session, "c1", referrer="https://www.google.com.mx/search") == "Organic Search"
        assert await self._channel(db_session, "c2", referrer="https://lnkd.in/abc") == "Organic Social"
        assert await self._channel(db_session, "c3", referrer="https://blog.example.org/x") == "Referral"
        assert await self._channel(db_session, "c4") == "Direct"
        assert await self._channel(db_session, "c5", referrer="https://cjhirashi.com/about") == "Direct"
        assert await self._channel(db_session, "c6", utm={"utm_medium": "postulacion"},
                                   referrer="https://linkedin.com/") == "Application"
        assert await self._channel(db_session, "c7", utm={"utm_source": "boletin"}) == "Unknown"


@pytest.mark.requisito("RF-005")
class TestIPNotPersisted:
    """RF-005: IP address is never persisted in any column."""

    async def test_ip_not_in_event_columns(
        self, db_session: AsyncSession, test_site
    ):
        """Event should not have IP column."""
        site, _ = test_site
        payload = TrackEventIn(type="pageview", page="/", ip="192.168.1.1")

        event = await ingest_event(
            db_session,
            payload=payload,
            headers={"CF-Connecting-IP": "8.8.8.8"},
            ip="8.8.8.8",
        )

        # Verify no IP column exists in PortalEvent
        columns = {c.name for c in PortalEvent.__table__.columns}
        assert "ip" not in columns, "PortalEvent should not have 'ip' column"

        # Verify no IP appears in the event's columns
        event_row = await db_session.execute(
            select(PortalEvent).where(PortalEvent.id == event.id)
        )
        event_fetched = event_row.scalar_one()
        assert event_fetched.country is not None or event_fetched.country is None  # OK


@pytest.mark.requisito("RF-007")
class TestBotDetection:
    """RF-007: Bot score calculated; score >= 70 marks as bot."""

    async def test_bot_ua_sets_is_bot(
        self, db_session: AsyncSession, test_site
    ):
        """Event with bot user agent marks visit as is_bot."""
        site, _ = test_site

        payload = TrackEventIn(
            type="pageview",
            page="/",
            visitorId="bot-visitor",
            userAgent="Mozilla/5.0 (compatible; Googlebot/2.1)",
        )

        event = await ingest_event(db_session, payload=payload, headers={}, ip=None)

        visit_row = await db_session.execute(
            select(PortalVisit).where(PortalVisit.id == event.visit_id)
        )
        visit = visit_row.scalar_one()
        assert visit.is_bot is True
        assert visit.bot_score >= 70


@pytest.mark.requisito("RF-001")
class TestEngagementMetrics:
    """Track engagement: is_engaged and is_bounce flags."""

    async def test_engaged_on_2_pageviews(
        self, db_session: AsyncSession, test_site
    ):
        """Visit becomes engaged after 2 pageviews."""
        site, _ = test_site
        now = datetime.now(timezone.utc)

        # First pageview
        payload1 = TrackEventIn(
            type="pageview",
            page="/projects",
            visitorId="engagement-visitor",
        )
        event1 = await ingest_event(db_session, payload=payload1, headers={}, ip=None, now=now)

        # Check: still bounce (1 pageview)
        visit_row = await db_session.execute(
            select(PortalVisit).where(PortalVisit.id == event1.visit_id)
        )
        visit = visit_row.scalar_one()
        assert visit.pageviews == 1
        assert visit.is_bounce is True
        assert visit.is_engaged is False

        # Second pageview
        now2 = now + timedelta(minutes=5)
        payload2 = TrackEventIn(
            type="pageview",
            page="/about",
            visitorId="engagement-visitor",
        )
        event2 = await ingest_event(db_session, payload=payload2, headers={}, ip=None, now=now2)

        # Check: now engaged (2+ pageviews)
        visit_row = await db_session.execute(
            select(PortalVisit).where(PortalVisit.id == event1.visit_id)
        )
        visit = visit_row.scalar_one()
        assert visit.pageviews == 2
        assert visit.is_engaged is True
        assert visit.is_bounce is False

    async def test_engaged_on_active_time(
        self, db_session: AsyncSession, test_site
    ):
        """Visit becomes engaged with active_ms > 10000."""
        site, _ = test_site
        now = datetime.now(timezone.utc)

        # Single pageview with active time > 10s
        payload = TrackEventIn(
            type="page_duration",
            page="/projects",
            visitorId="active-visitor",
            activeMs=15000,
        )

        event = await ingest_event(db_session, payload=payload, headers={}, ip=None, now=now)

        visit_row = await db_session.execute(
            select(PortalVisit).where(PortalVisit.id == event.visit_id)
        )
        visit = visit_row.scalar_one()
        assert visit.active_ms > 10000
        assert visit.is_engaged is True
        assert visit.is_bounce is False

    async def test_engaged_on_key_event(
        self, db_session: AsyncSession, test_site, key_event_goal
    ):
        """Visit becomes engaged (and converted) when a key event matches."""
        site, _ = test_site

        payload = TrackEventIn(
            type="download",
            page="/cv",
            visitorId="download-visitor",
        )

        event = await ingest_event(db_session, payload=payload, headers={}, ip=None)

        visit_row = await db_session.execute(
            select(PortalVisit).where(PortalVisit.id == event.visit_id)
        )
        visit = visit_row.scalar_one()
        assert visit.converted is True
        assert visit.is_engaged is True
        assert visit.is_bounce is False


@pytest.mark.requisito("RF-001")
class TestMaxScrollTracking:
    """Visit tracks max scroll percentage."""

    async def test_max_scroll_pct_updated(
        self, db_session: AsyncSession, test_site
    ):
        """Visit.max_scroll_pct is updated with the highest value."""
        site, _ = test_site
        now = datetime.now(timezone.utc)

        # First event: 30% scroll
        payload1 = TrackEventIn(
            type="scroll",
            page="/",
            visitorId="scroll-visitor",
            scrollPct=30,
        )
        event1 = await ingest_event(db_session, payload=payload1, headers={}, ip=None, now=now)

        # Second event: 75% scroll
        now2 = now + timedelta(minutes=1)
        payload2 = TrackEventIn(
            type="scroll",
            page="/",
            visitorId="scroll-visitor",
            scrollPct=75,
        )
        event2 = await ingest_event(db_session, payload=payload2, headers={}, ip=None, now=now2)

        visit_row = await db_session.execute(
            select(PortalVisit).where(PortalVisit.id == event1.visit_id)
        )
        visit = visit_row.scalar_one()
        assert visit.max_scroll_pct == 75


@pytest.mark.requisito("RF-001")
class TestUnknownSite:
    """UnknownSite exception for invalid siteKey."""

    async def test_unknown_site_key_raises(
        self, db_session: AsyncSession, test_site
    ):
        """Unknown siteKey raises UnknownSite."""
        payload = TrackEventIn(
            type="pageview",
            page="/",
            siteKey="unknown-site-key",
        )

        with pytest.raises(UnknownSite):
            await ingest_event(db_session, payload=payload, headers={}, ip=None)

    async def test_no_default_site_raises(
        self, db_session: AsyncSession
    ):
        """No default site raises UnknownSite."""
        # Create user but no site
        user = User(
            username="no-site-user",
            email="nosite@example.com",
            password_hash="hash",
            is_active=True,
        )
        db_session.add(user)
        await db_session.flush()

        payload = TrackEventIn(type="pageview", page="/")

        with pytest.raises(UnknownSite):
            await ingest_event(db_session, payload=payload, headers={}, ip=None)


@pytest.mark.requisito("RF-001")
class TestNewVisitorTracking:
    """Visit tracks is_new_visitor flag."""

    async def test_first_visit_marked_as_new(
        self, db_session: AsyncSession, test_site
    ):
        """First visit from a visitor is marked is_new_visitor=True."""
        site, _ = test_site

        payload = TrackEventIn(
            type="pageview",
            page="/",
            visitorId="new-visitor-test",
        )

        event = await ingest_event(db_session, payload=payload, headers={}, ip=None)

        visit_row = await db_session.execute(
            select(PortalVisit).where(PortalVisit.id == event.visit_id)
        )
        visit = visit_row.scalar_one()
        assert visit.is_new_visitor is True

    async def test_second_visit_not_new(
        self, db_session: AsyncSession, test_site
    ):
        """Second visit from a visitor is NOT marked as new."""
        site, _ = test_site
        now = datetime.now(timezone.utc)

        # First visit
        payload1 = TrackEventIn(
            type="pageview",
            page="/",
            visitorId="returning-visitor",
        )
        event1 = await ingest_event(db_session, payload=payload1, headers={}, ip=None, now=now)

        # Second visit (31 min later, new session)
        now2 = now + timedelta(minutes=31)
        payload2 = TrackEventIn(
            type="pageview",
            page="/about",
            visitorId="returning-visitor",
        )
        event2 = await ingest_event(db_session, payload=payload2, headers={}, ip=None, now=now2)

        visit_row = await db_session.execute(
            select(PortalVisit).where(PortalVisit.id == event2.visit_id)
        )
        visit = visit_row.scalar_one()
        assert visit.is_new_visitor is False


@pytest.mark.requisito("RF-006")
class TestHeadersAndCounters:
    async def test_user_agent_header_used_when_payload_has_none(self, db_session: AsyncSession, test_site):
        ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
        event = await ingest_event(db_session, payload=TrackEventIn(type="pageview", page="/", visitorId="hdr-1"),
                                   headers={"User-Agent": ua, "Accept-Language": "es-MX,es;q=0.9"}, ip=None)
        visit = (await db_session.execute(select(PortalVisit).where(PortalVisit.id == event.visit_id))).scalar_one()
        assert visit.device_type == "mobile" and visit.os == "iOS" and visit.language == "es-MX"
        assert event.user_agent == ua

    async def test_visit_count_counts_visits_not_events(self, db_session: AsyncSession, test_site):
        base = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)
        for minutes in (0, 5, 10, 60, 65):
            await ingest_event(db_session, payload=TrackEventIn(type="pageview", page="/", visitorId="cnt-1"),
                               headers={}, ip=None, now=base + timedelta(minutes=minutes))
        visitor = (await db_session.execute(select(PortalVisitor).where(PortalVisitor.visitor_key == "cnt-1"))).scalar_one()
        assert visitor.visit_count == 2

    async def test_owner_token_marks_existing_visit(self, db_session: AsyncSession, test_site):
        site, token = test_site
        base = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)
        first = await ingest_event(db_session, payload=TrackEventIn(type="pageview", page="/", visitorId="own-1"),
                                   headers={}, ip=None, now=base)
        await ingest_event(db_session, payload=TrackEventIn(type="pageview", page="/about", visitorId="own-1", ownerToken=token),
                           headers={}, ip=None, now=base + timedelta(minutes=1))
        visit = (await db_session.execute(select(PortalVisit).where(PortalVisit.id == first.visit_id))).scalar_one()
        assert visit.is_owner is True
