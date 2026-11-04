"""Motor de métricas (SPEC-0010 D3-D7) contra datos sintéticos de resultado calculado a mano.

Ventana: 2026-10-01 a 2026-10-03. Visitas limpias: V1 (A, 2 págs, 20 s), V2 (B, rebote),
V3 (A, rebote), V4 (C, convertida, 5 s), V6 (F, rebote). Excluidas: un bot (V5) y una visita del dueño (V8).
"""
from datetime import date, datetime, timezone

import pytest
from sqlalchemy import select

from config import settings
from models import (PortalDaily, PortalEvent, PortalFunnel, PortalGoal, PortalSite, PortalVisit, PortalVisitor, User)
from services import portal_metrics as pm

UID = settings.PUBLIC_PORTAL_USER_ID
SINCE, UNTIL = date(2026, 10, 1), date(2026, 10, 3)


def ts(day: int, hour: int = 18, month: int = 10) -> datetime:
    return datetime(2026, month, day, hour, 0, tzinfo=timezone.utc)  # 12:00 en CDMX


@pytest.fixture
async def seeded(db_session):
    db = db_session
    db.add(User(id=UID, username="metrics-user", email="m@example.com", password_hash="x", is_active=True))
    await db.flush()
    site = PortalSite(user_id=UID, name="s", domain="cjhirashi.com", public_key="k", owner_token_hash="0" * 64,
                      allowed_hosts=["cjhirashi.com"], timezone="America/Mexico_City", active=True)
    db.add(site)
    await db.flush()

    visitors = {}
    for key, first, bot, owner in [("A", ts(1), False, False), ("B", ts(1), False, False), ("C", ts(2), False, False),
                                   ("D", ts(2), True, False), ("E", ts(3), False, True), ("F", ts(1), False, False)]:
        v = PortalVisitor(user_id=UID, site_id=site.id, visitor_key=key, first_seen=first, last_seen=first,
                          visit_count=1, is_bot=bot, is_owner=owner)
        db.add(v)
        visitors[key] = v
    await db.flush()

    def visit(vkey, when, channel, pageviews, active, *, entry="/", exit_="/", new=True, engaged=False, converted=False,
              bot=False, owner=False, country="Mexico", device="desktop", campaign=None, application_id=None):
        row = PortalVisit(
            user_id=UID, site_id=site.id, visitor_id=visitors[vkey].id, started_at=when, last_activity_at=when,
            entry_page=entry, exit_page=exit_, channel=channel, country=country, device_type=device,
            pageviews=pageviews, events_count=pageviews, active_ms=active, is_engaged=engaged, is_bounce=not engaged,
            converted=converted, is_bot=bot, is_owner=owner, is_new_visitor=new, utm_campaign=campaign,
            application_id=application_id, updated_at=when,
        )
        db.add(row)
        return row

    v1 = visit("A", ts(1), "Organic Search", 2, 20000, exit_="/projects/x", engaged=True)
    v2 = visit("B", ts(1), "Direct", 1, 2000, device="mobile")
    v3 = visit("A", ts(2), "Organic Social", 1, 0, entry="/about", exit_="/about", new=False)
    v4 = visit("C", ts(2), "Application", 1, 5000, engaged=True, converted=True, campaign="apl-1")
    v5 = visit("D", ts(2), "Direct", 1, 0, bot=True)
    v6 = visit("F", ts(1), "Referral", 1, 0, entry="/about", exit_="/about", country="Spain")
    v7 = visit("F", ts(8), "Direct", 1, 0, new=False)  # fuera de la ventana; da la retención de la semana siguiente
    v8 = visit("E", ts(3), "Direct", 1, 0, owner=True)
    await db.flush()

    def event(vis, seq, kind, page, **extra):
        db.add(PortalEvent(user_id=UID, site_id=site.id, visitor_id=vis.visitor_id, visit_id=vis.id, seq=seq,
                           event_type=kind, page=page, created_at=vis.started_at, **extra))

    event(v1, 1, "pageview", "/"); event(v1, 2, "pageview", "/projects/x"); event(v1, 3, "page_duration", "/projects/x", active_ms=20000)
    event(v2, 1, "pageview", "/"); event(v2, 2, "page_duration", "/", duration_ms=2000)
    event(v3, 1, "pageview", "/about")
    event(v4, 1, "pageview", "/"); event(v4, 2, "download", "/", target="cv.pdf"); event(v4, 3, "page_duration", "/", active_ms=5000)
    event(v5, 1, "pageview", "/")
    event(v6, 1, "pageview", "/about", scroll_pct=80)
    event(v8, 1, "pageview", "/")
    db.add(PortalGoal(user_id=UID, site_id=site.id, name="cv_download", type="event", match={"event_type": "download"}, is_key_event=True))
    funnel = PortalFunnel(user_id=UID, site_id=site.id, name="Home a proyecto",
                          steps=[{"label": "Home", "type": "page", "match": {"path_prefix": "/"}},
                                 {"label": "Proyecto", "type": "page", "match": {"path_prefix": "/projects/"}}])
    db.add(funnel)
    await db.flush()
    return site, funnel


def query(site, **kw):
    return pm.MetricsQuery(UID, site, kw.pop("since", SINCE), kw.pop("until", UNTIL), **kw)


@pytest.mark.requisito("RF-033")
async def test_kpis_exclude_bots_and_owner(db_session, seeded):
    site, _ = seeded
    k = await pm.kpis(db_session, query(site))
    assert (k["visitors"], k["visits"], k["pageviews"]) == (4, 5, 6)
    assert k["bounce_rate"] == 0.6 and k["engagement_rate"] == 0.4
    assert k["pages_per_visit"] == 1.2
    assert k["median_active_ms"] == 2000 and k["p90_active_ms"] == 14000
    assert (k["converted_visits"], k["converting_visitors"], k["conversion_rate"]) == (1, 1, 0.25)
    assert (k["new_visitors"], k["returning_visitors"]) == (4, 0)


@pytest.mark.requisito("RF-033")
async def test_exclusion_flags_can_be_disabled(db_session, seeded):
    site, _ = seeded
    assert (await pm.kpis(db_session, query(site, exclude_bots=False)))["visits"] == 6
    assert (await pm.kpis(db_session, query(site, exclude_owner=False)))["visits"] == 6
    assert (await pm.kpis(db_session, query(site, exclude_bots=False, exclude_owner=False)))["visits"] == 7


@pytest.mark.requisito("RF-033")
async def test_filters_and_unknown_filter(db_session, seeded):
    site, _ = seeded
    assert (await pm.kpis(db_session, query(site, filters={"country": "Spain"})))["visits"] == 1
    assert (await pm.kpis(db_session, query(site, filters={"channel": ["Direct", "Referral"]})))["visits"] == 2
    with pytest.raises(ValueError):
        await pm.kpis(db_session, query(site, filters={"no_existe": 1}))


@pytest.mark.requisito("RF-033")
async def test_breakdown_by_channel(db_session, seeded):
    site, _ = seeded
    rows = {r["key"]: r for r in await pm.breakdown(db_session, query(site), "channel")}
    assert set(rows) == {"Organic Search", "Direct", "Organic Social", "Application", "Referral"}
    assert rows["Application"]["converted_visits"] == 1 and rows["Direct"]["share"] == 0.2
    with pytest.raises(ValueError):
        await pm.breakdown(db_session, query(site), "password")


@pytest.mark.requisito("RF-033")
async def test_pages_paths_and_scroll(db_session, seeded):
    site, _ = seeded
    by_page = {r["page"]: r for r in await pm.pages(db_session, query(site))}
    home = by_page["/"]
    assert (home["pageviews"], home["visitors"], home["entries"], home["exits"]) == (3, 3, 3, 2)
    assert home["exit_rate"] == 0.6667
    assert by_page["/about"]["avg_max_scroll_pct"] == 80.0
    assert by_page["/projects/x"]["median_active_ms"] == 20000
    assert await pm.paths(db_session, query(site)) == [{"from_page": "/", "to_page": "/projects/x", "count": 1}]


@pytest.mark.requisito("RF-033")
async def test_goals_and_funnel(db_session, seeded):
    site, funnel = seeded
    goals = await pm.goals(db_session, query(site))
    assert goals[0]["converted_visits"] == 1 and goals[0]["conversion_rate"] == 0.25
    steps = await pm.funnel(db_session, query(site), funnel)
    # El prefijo "/" cubre toda página: 5 visitas limpias con alguna vista; solo V1 llega después a /projects/.
    assert [s["visits"] for s in steps] == [5, 1]
    assert steps[1]["from_previous"] == 0.2 and steps[1]["from_start"] == 0.2


@pytest.mark.requisito("RF-033")
async def test_retention_weekly_cohort(db_session, seeded):
    site, _ = seeded
    rows = await pm.retention(db_session, query(site), weeks=4)
    assert rows == [{"cohort_week": date(2026, 9, 28), "size": 4, "active_by_week": [4, 1, 0, 0, 0]}]


@pytest.mark.requisito("RF-034")
async def test_compare_periods():
    class Q:  # solo `since`, `until` y `days` participan
        since, until, days = date(2026, 10, 8), date(2026, 10, 14), 7
    assert pm.compare_period(Q, "previous") == (date(2026, 10, 1), date(2026, 10, 7))
    assert pm.compare_period(Q, "year") == (date(2025, 10, 8), date(2025, 10, 14))
    assert pm.compare_period(Q, "weekday") == (date(2026, 10, 1), date(2026, 10, 7))
    assert pm.compare_period(Q, "none") is None
    with pytest.raises(ValueError):
        pm.compare_period(Q, "mañana")
    Q.since, Q.until, Q.days = date(2024, 2, 29), date(2024, 3, 2), 3
    assert pm.compare_period(Q, "year")[0] == date(2023, 2, 28)


@pytest.mark.requisito("RF-034")
async def test_deltas():
    d = pm.deltas({"visits": 5, "bounce_rate": None}, {"visits": 0, "bounce_rate": 0.5})
    assert d["visits"] == {"current": 5, "previous": 0, "delta_abs": 5, "delta_pct": None}
    assert d["bounce_rate"]["delta_abs"] is None


@pytest.mark.requisito("RF-036")
async def test_daily_trend_from_portal_daily_and_staleness(db_session, seeded):
    site, _ = seeded
    q = query(site)
    points = {p["bucket"]: p for p in await pm.trend(db_session, q, "day")}
    assert [(points[date(2026, 10, d)]["visits"], points[date(2026, 10, d)]["visitors"]) for d in (1, 2, 3)] == [(3, 3), (2, 2), (0, 0)]
    stored = (await db_session.execute(select(PortalDaily).where(PortalDaily.dimension == "total"))).scalars().all()
    assert {r.day: r.visits for r in stored} == {date(2026, 10, 1): 3, date(2026, 10, 2): 2}

    # Una visita nueva con `updated_at` posterior vuelve vieja la caché del día y se recalcula.
    visitor = (await db_session.execute(select(PortalVisitor).where(PortalVisitor.visitor_key == "B"))).scalar_one()
    db_session.add(PortalVisit(user_id=UID, site_id=site.id, visitor_id=visitor.id, started_at=ts(2, 20), last_activity_at=ts(2, 20),
                               entry_page="/", pageviews=1, events_count=1, updated_at=datetime.now(timezone.utc)))
    await db_session.flush()
    points = {p["bucket"]: p for p in await pm.trend(db_session, q, "day")}
    assert points[date(2026, 10, 2)]["visits"] == 3


@pytest.mark.requisito("RF-036")
async def test_trend_with_filters_reads_live(db_session, seeded):
    site, _ = seeded
    points = await pm.trend(db_session, query(site, filters={"channel": "Direct"}), "day")
    assert sum(p["visits"] for p in points) == 1


@pytest.mark.requisito("RF-033")
async def test_realtime_counts_recent_clean_visitors(db_session, seeded):
    site, _ = seeded
    visitor = (await db_session.execute(select(PortalVisitor).where(PortalVisitor.visitor_key == "B"))).scalar_one()
    now = datetime.now(timezone.utc)
    db_session.add(PortalVisit(user_id=UID, site_id=site.id, visitor_id=visitor.id, started_at=now, last_activity_at=now,
                               entry_page="/", exit_page="/projects/y", pageviews=1, events_count=1))
    await db_session.flush()
    out = await pm.realtime(db_session, UID, site)
    assert out["visitors_now"] == 1 and out["top_pages"] == [{"page": "/projects/y", "visitors": 1}]


@pytest.mark.requisito("RF-033")
async def test_funnel_requires_steps_in_order(db_session, seeded):
    site, funnel = seeded
    funnel.steps = [{"label": "Proyecto", "type": "page", "match": {"path_prefix": "/projects/"}},
                    {"label": "Luego otra vista", "type": "page", "match": {"path_prefix": "/"}}]
    await db_session.flush()
    steps = await pm.funnel(db_session, query(site), funnel)
    # V1 llegó a /projects/x pero no vio ninguna página DESPUÉS: el orden cuenta.
    assert [s["visits"] for s in steps] == [1, 0]


@pytest.mark.requisito("RF-022")
async def test_rebuild_visits_reclassifies_channel_and_recounts(db_session, seeded):
    from models import PortalChannelRule
    site, _ = seeded
    # Una regla nueva: todo referrer de blog.example.org pasa a "Referral"; V1 vino de Google.
    v1 = (await db_session.execute(select(PortalVisit).where(PortalVisit.channel == "Organic Search"))).scalar_one()
    v1.referrer_domain = "blog.example.org"
    v1.pageviews = 99          # contador dañado a propósito: el crudo debe corregirlo
    v1.is_engaged, v1.is_bounce = False, True
    db_session.add(PortalChannelRule(user_id=UID, site_id=site.id, priority=0, channel="Referral",
                                     conditions={"referrer_domain_in": ["blog.example.org"]}))
    await db_session.flush()
    count = await pm.rebuild_visits(db_session, UID, site, SINCE, UNTIL)
    await db_session.refresh(v1)
    assert count == 7  # V1-V6 y V8 caen en el rango (bots y dueño incluidos); V7 es del día 8
    assert v1.channel == "Referral" and v1.pageviews == 2 and v1.is_engaged is True and v1.active_ms == 20000
    events = (await db_session.execute(select(PortalEvent))).scalars().all()
    assert len(events) == 12  # el crudo no cambia


@pytest.mark.requisito("RF-020")
def test_only_forget_deletes_raw_analytics_rows():
    """Ninguna ruta ni servicio borra eventos, visitas o visitantes salvo /events/forget."""
    import re
    from pathlib import Path
    deleters = set()
    for path in Path(__file__).resolve().parents[2].joinpath("src").rglob("*.py"):
        text = path.read_text()
        if re.search(r"delete\(\s*Portal(Event|Visit|Visitor)\b", text) or re.search(r"DELETE\s+FROM\s+portal_(events|visits|visitors)\b", text, re.I) \
                or re.search(r"session\.delete\(|db\.delete\(", text) and re.search(r"Portal(Event|Visit|Visitor)", text) and "portal" in path.name:
            deleters.add(path.name)
    assert deleters == {"events.py"}, deleters
