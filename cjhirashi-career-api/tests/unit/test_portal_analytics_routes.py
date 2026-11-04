"""Rutas de solo lectura y CRUD de la analítica del portafolio (SPEC-0010 D1-D2)."""
from datetime import date, datetime, timedelta, timezone

import pytest
from httpx import ASGITransport, AsyncClient

from app import app
from database import get_db
from middleware.auth import get_current_user
from models.portal_annotation import PortalAnnotation
from models.portal_daily import PortalDaily
from models.portal_event import PortalEvent
from models.portal_funnel import PortalFunnel
from models.portal_goal import PortalGoal
from models.portal_site import PortalSite
from models.portal_visit import PortalVisit
from models.portal_visitor import PortalVisitor
from models.user import User
from services.auth_service import AuthService

BASE = "/career"


def _as(db_session, user: User) -> None:
    async def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: user


@pytest.fixture
async def api(db_session, test_user: User):
    _as(db_session, test_user)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
async def test_user2(db_session):
    user = User(
        username="testuser2",
        email="test2@example.com",
        password_hash=AuthService.hash_password("TestPassword123!"),
        full_name="Test User 2",
        professional_title="Developer",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def portal_site_1(db_session, test_user: User):
    site = PortalSite(
        user_id=test_user.id,
        name="Test Site 1",
        domain="testsite1.com",
        public_key="test_key_1_24_chars",
        owner_token_hash="a" * 64,
        allowed_hosts=["testsite1.com"],
        timezone="America/Mexico_City",
        active=True,
    )
    db_session.add(site)
    await db_session.flush()
    await db_session.refresh(site)
    return site


@pytest.fixture
async def portal_visitors_1(db_session, test_user: User, portal_site_1: PortalSite):
    now = datetime.now(timezone.utc)
    visitors = []
    for i in range(3):
        v = PortalVisitor(
            user_id=test_user.id,
            site_id=portal_site_1.id,
            visitor_key=f"visitor_{i}",
            first_seen=now - timedelta(days=i),
            last_seen=now - timedelta(days=i),
            visit_count=1,
        )
        db_session.add(v)
        visitors.append(v)
    await db_session.flush()
    for v in visitors:
        await db_session.refresh(v)
    return visitors


@pytest.fixture
async def portal_visits_1(db_session, test_user: User, portal_site_1: PortalSite, portal_visitors_1):
    now = datetime.now(timezone.utc)
    pages = ["/index.html", "/proyectos", "/cv"]
    visits = []
    for i, visitor in enumerate(portal_visitors_1):
        v = PortalVisit(
            user_id=test_user.id,
            site_id=portal_site_1.id,
            visitor_id=visitor.id,
            started_at=now - timedelta(days=i),
            last_activity_at=now - timedelta(days=i),
            entry_page=pages[i],
            pageviews=i + 1,
            is_engaged=True,
        )
        db_session.add(v)
        visits.append(v)
    await db_session.flush()
    for v in visits:
        await db_session.refresh(v)
    return visits


@pytest.fixture
async def portal_events_1(db_session, test_user: User, portal_site_1: PortalSite, portal_visitors_1, portal_visits_1):
    now = datetime.now(timezone.utc)
    events = []
    for i in range(5):
        e = PortalEvent(
            user_id=test_user.id,
            event_type="pageview",
            page="/index.html",
            site_id=portal_site_1.id,
            visitor_id=portal_visitors_1[0].id,
            visit_id=portal_visits_1[0].id,
            created_at=now - timedelta(hours=i),
        )
        db_session.add(e)
        events.append(e)
    await db_session.flush()
    for e in events:
        await db_session.refresh(e)
    return events


@pytest.fixture
async def portal_daily_1(db_session, test_user: User, portal_site_1: PortalSite):
    today = datetime.now(timezone.utc).date()
    rollups = []
    for i in range(3):
        d = PortalDaily(
            user_id=test_user.id,
            site_id=portal_site_1.id,
            day=today - timedelta(days=i),
            dimension="total",
            key="",
            visitors=10 * (i + 1),
            visits=20 * (i + 1),
            pageviews=50 * (i + 1),
        )
        db_session.add(d)
        rollups.append(d)
    await db_session.flush()
    for d in rollups:
        await db_session.refresh(d)
    return rollups


@pytest.fixture
async def goal_1(db_session, test_user: User, portal_site_1: PortalSite):
    goal = PortalGoal(
        user_id=test_user.id,
        site_id=portal_site_1.id,
        name="Descarga de CV",
        type="event",
        match={"event_type": "download"},
        is_key_event=True,
    )
    db_session.add(goal)
    await db_session.flush()
    await db_session.refresh(goal)
    return goal


# ============================================================================
# D1: solo lectura
# ============================================================================

@pytest.mark.requisito("RF-030")
async def test_portal_sites_list_omits_keys(api, portal_site_1: PortalSite):
    r = await api.get(f"{BASE}/portal-sites")
    assert r.status_code == 200
    body = r.json()
    assert [s["domain"] for s in body] == ["testsite1.com"]
    assert "public_key" not in body[0] and "owner_token_hash" not in body[0]


@pytest.mark.requisito("RF-030")
async def test_portal_sites_count_and_get(api, portal_site_1: PortalSite):
    assert (await api.get(f"{BASE}/portal-sites/count")).json() == {"count": 1}
    r = await api.get(f"{BASE}/portal-sites/{portal_site_1.id}")
    assert r.status_code == 200 and r.json()["id"] == portal_site_1.id
    assert (await api.get(f"{BASE}/portal-sites/psi_no_existe")).status_code == 404


@pytest.mark.requisito("RF-030")
async def test_read_only_resources_reject_writes(api, portal_site_1, portal_visits_1, portal_events_1):
    for resource, item in [
        ("portal-sites", portal_site_1.id),
        ("portal-visits", portal_visits_1[0].id),
        ("portal-events", portal_events_1[0].id),
    ]:
        assert (await api.post(f"{BASE}/{resource}", json={})).status_code == 405
        assert (await api.put(f"{BASE}/{resource}/{item}", json={})).status_code == 405
        assert (await api.delete(f"{BASE}/{resource}/{item}")).status_code == 405


@pytest.mark.requisito("RF-030")
async def test_visitors_default_sort_is_last_seen_desc(api, portal_visitors_1):
    body = (await api.get(f"{BASE}/portal-visitors")).json()
    assert [v["visitor_key"] for v in body] == ["visitor_0", "visitor_1", "visitor_2"]


@pytest.mark.requisito("RF-030")
async def test_visitors_pagination(api, portal_visitors_1):
    body = (await api.get(f"{BASE}/portal-visitors", params={"skip": 2, "limit": 2})).json()
    assert [v["visitor_key"] for v in body] == ["visitor_2"]


@pytest.mark.requisito("RF-030")
async def test_visits_since_until_by_day(api, portal_visits_1):
    since = (datetime.now(timezone.utc) - timedelta(days=1)).date().isoformat()
    r = await api.get(f"{BASE}/portal-visits/count", params={"since": since})
    assert r.json() == {"count": 2}


@pytest.mark.requisito("RF-030")
async def test_visits_filter_valid_and_invalid_column(api, portal_visits_1):
    r = await api.get(f"{BASE}/portal-visits", params={"filters": '{"entry_page": "/proyectos"}'})
    assert r.status_code == 200 and [v["entry_page"] for v in r.json()] == ["/proyectos"]
    r = await api.get(f"{BASE}/portal-visits", params={"filters": '{"entry_page": ["/cv", "/proyectos"]}'})
    assert r.status_code == 200 and len(r.json()) == 2
    r = await api.get(f"{BASE}/portal-visits", params={"filters": '{"no_existe": 1}'})
    assert r.status_code == 400


@pytest.mark.requisito("RF-030")
async def test_sort_by_rejects_non_column(api, portal_visits_1):
    r = await api.get(f"{BASE}/portal-visits", params={"sort_by": "metadata"})
    assert r.status_code == 400


@pytest.mark.requisito("RF-030")
async def test_events_list_exposes_visit_link(api, portal_events_1):
    body = (await api.get(f"{BASE}/portal-events")).json()
    assert len(body) == 5 and all(e["visit_id"] for e in body)


@pytest.mark.requisito("RF-030")
async def test_daily_since_until_compares_by_day(api, portal_daily_1):
    today = datetime.now(timezone.utc).date()
    r = await api.get(
        f"{BASE}/portal-daily",
        params={"since": (today - timedelta(days=1)).isoformat(), "until": today.isoformat()},
    )
    assert r.status_code == 200
    assert sorted(d["day"] for d in r.json()) == sorted(
        [(today - timedelta(days=1)).isoformat(), today.isoformat()]
    )


@pytest.mark.requisito("RF-030")
async def test_isolation_user2_sees_no_user1_data(db_session, api, test_user2: User, portal_site_1, portal_visits_1):
    _as(db_session, test_user2)
    assert (await api.get(f"{BASE}/portal-sites")).json() == []
    assert (await api.get(f"{BASE}/portal-visits")).json() == []
    assert (await api.get(f"{BASE}/portal-sites/{portal_site_1.id}")).status_code == 404


@pytest.mark.requisito("RF-030")
async def test_read_routes_require_auth(db_session):
    app.dependency_overrides.clear()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as anon:
        r = await anon.get(f"{BASE}/portal-sites")
    assert r.status_code in (401, 403)


# ============================================================================
# D2: configuración CRUD (metas, embudos, anotaciones)
# ============================================================================

@pytest.mark.requisito("RF-031")
async def test_goals_create_read_update_delete(api, portal_site_1: PortalSite):
    payload = {
        "site_id": portal_site_1.id,
        "name": "Contacto",
        "type": "event",
        "match": {"event_type": "form_submit"},
        "is_key_event": True,
    }
    created = await api.post(f"{BASE}/portal-goals", json=payload)
    assert created.status_code == 201
    goal_id = created.json()["id"]
    assert (await api.get(f"{BASE}/portal-goals/{goal_id}")).json()["name"] == "Contacto"
    updated = await api.put(f"{BASE}/portal-goals/{goal_id}", json={"is_key_event": False})
    assert updated.status_code == 200 and updated.json()["is_key_event"] is False
    assert (await api.delete(f"{BASE}/portal-goals/{goal_id}")).status_code == 204
    assert (await api.get(f"{BASE}/portal-goals/{goal_id}")).status_code == 404


@pytest.mark.requisito("RF-031")
async def test_goals_invalid_type_rejected(api, portal_site_1: PortalSite):
    r = await api.post(
        f"{BASE}/portal-goals",
        json={"site_id": portal_site_1.id, "name": "X", "type": "magia", "match": {}},
    )
    assert r.status_code == 422


@pytest.mark.requisito("RF-031")
async def test_goals_list_includes_seeded(api, goal_1):
    body = (await api.get(f"{BASE}/portal-goals")).json()
    assert [g["name"] for g in body] == ["Descarga de CV"]


@pytest.mark.requisito("RF-031")
async def test_funnel_requires_two_steps(api, portal_site_1: PortalSite):
    one_step = {
        "site_id": portal_site_1.id,
        "name": "Embudo corto",
        "steps": [{"label": "Inicio", "type": "page", "match": {"prefix": "/"}}],
    }
    assert (await api.post(f"{BASE}/portal-funnels", json=one_step)).status_code == 422

    two_steps = {**one_step, "steps": one_step["steps"] + [{"label": "CV", "type": "page", "match": {"prefix": "/cv"}}]}
    created = await api.post(f"{BASE}/portal-funnels", json=two_steps)
    assert created.status_code == 201 and len(created.json()["steps"]) == 2


@pytest.mark.requisito("RF-031")
async def test_annotations_create_and_list(api, portal_site_1: PortalSite):
    payload = {
        "site_id": portal_site_1.id,
        "day": date.today().isoformat(),
        "title": "Publicación: migración a Postgres",
        "kind": "blog_post",
        "ref": "/blog/migracion",
    }
    assert (await api.post(f"{BASE}/portal-annotations", json=payload)).status_code == 201
    body = (await api.get(f"{BASE}/portal-annotations")).json()
    assert [a["title"] for a in body] == ["Publicación: migración a Postgres"]


@pytest.mark.requisito("RF-031")
async def test_annotations_invalid_kind_rejected(api, portal_site_1: PortalSite):
    r = await api.post(
        f"{BASE}/portal-annotations",
        json={"site_id": portal_site_1.id, "day": "2026-11-04", "title": "X", "kind": "rumor"},
    )
    assert r.status_code == 422
