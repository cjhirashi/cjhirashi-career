"""Resumen diario perezoso (RF-036): peticiones simultáneas del tablero no deben chocar al recalcular."""
import asyncio
from datetime import date, datetime, timezone

import pytest
from sqlalchemy import func, select

from config import settings
from models import PortalDaily, PortalSite, PortalVisit, PortalVisitor, User
from services import portal_metrics as pm

UID = settings.PUBLIC_PORTAL_USER_ID
SINCE, UNTIL = date(2026, 10, 1), date(2026, 10, 3)


@pytest.fixture
async def stale_site(test_db):
    async with test_db() as db:
        db.add(User(id=UID, username="daily-user", email="d@example.com", password_hash="x", is_active=True))
        await db.flush()
        site = PortalSite(user_id=UID, name="s", domain="cjhirashi.com", public_key="k", owner_token_hash="0" * 64,
                          allowed_hosts=["cjhirashi.com"], timezone="America/Mexico_City", active=True)
        db.add(site)
        await db.flush()
        for n, day in enumerate((1, 2, 3)):
            when = datetime(2026, 10, day, 18, 0, tzinfo=timezone.utc)
            visitor = PortalVisitor(user_id=UID, site_id=site.id, visitor_key=f"v{n}", first_seen=when, last_seen=when, visit_count=1)
            db.add(visitor)
            await db.flush()
            db.add(PortalVisit(user_id=UID, site_id=site.id, visitor_id=visitor.id, started_at=when, last_activity_at=when,
                               entry_page="/", exit_page="/", channel="Direct", pageviews=1, events_count=1, updated_at=when))
        await db.commit()
        return site.id


@pytest.mark.requisito("RF-036")
async def test_simultaneous_requests_rebuild_the_daily_summary_once_without_conflict(test_db, stale_site):
    async def request() -> int:
        async with test_db() as db:
            site = (await db.execute(select(PortalSite).where(PortalSite.id == stale_site))).scalar_one()
            return await pm.ensure_daily_fresh(db, pm.MetricsQuery(UID, site, SINCE, UNTIL))

    results = await asyncio.gather(*(request() for _ in range(6)), return_exceptions=True)

    errors = [r for r in results if isinstance(r, Exception)]
    assert not errors, errors
    # Solo la primera petición recalcula; las demás ven los días ya al día tras esperar el bloqueo.
    assert sorted(results, reverse=True)[0] == 3 and sum(1 for r in results if r) == 1

    async with test_db() as db:
        totals = (await db.execute(select(func.count()).where(PortalDaily.site_id == stale_site, PortalDaily.dimension == "total"))).scalar_one()
        assert totals == 3  # un renglón por día, sin duplicados


@pytest.mark.requisito("RF-036")
async def test_rebuild_endpoint_and_lazy_refresh_do_not_collide(test_db, stale_site):
    async def lazy() -> int:
        async with test_db() as db:
            site = (await db.execute(select(PortalSite).where(PortalSite.id == stale_site))).scalar_one()
            return await pm.ensure_daily_fresh(db, pm.MetricsQuery(UID, site, SINCE, UNTIL))

    async def forced() -> dict:
        async with test_db() as db:
            site = (await db.execute(select(PortalSite).where(PortalSite.id == stale_site))).scalar_one()
            result = await pm.rebuild_daily(db, UID, site, SINCE, UNTIL)
            await db.commit()
            return result

    results = await asyncio.gather(lazy(), forced(), lazy(), forced(), return_exceptions=True)
    assert not [r for r in results if isinstance(r, Exception)], results
