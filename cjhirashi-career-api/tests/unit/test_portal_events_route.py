"""Rutas públicas de ingesta (C3, C4): /events/track y /events/forget."""
import hashlib
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text

from app import app
from config import settings
from database import get_db
from models import PortalEvent, PortalSite, PortalVisit, PortalVisitor, User
from services.portal_ingest import origin_allowed
from services.portal_ratelimit import SlidingWindowLimiter

SITE_KEY = "route-test-key"
CLIENT_IP = "203.0.113.77"


@pytest.fixture
async def client(test_db):
    async with test_db() as setup:
        setup.add(User(id=settings.PUBLIC_PORTAL_USER_ID, username="route-user", email="route@example.com",
                       password_hash="x", is_active=True))
        await setup.flush()
        setup.add(PortalSite(user_id=settings.PUBLIC_PORTAL_USER_ID, name="s", domain="cjhirashi.com",
                             public_key=SITE_KEY, owner_token_hash=hashlib.sha256(b"t").hexdigest(),
                             allowed_hosts=["cjhirashi.com"], active=True))
        await setup.commit()

    async def override_get_db():
        async with test_db() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with patch("services.portal_geo.settings.GEO_SOURCE", "cf"):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            c.test_db = test_db
            yield c
    app.dependency_overrides.pop(get_db, None)


async def _count(client, model):
    async with client.test_db() as s:
        return len((await s.execute(select(model))).scalars().all())


@pytest.mark.requisito("RF-001")
async def test_v1_payload_is_accepted(client):
    r = await client.post("/events/track", json={"type": "pageview", "page": "/", "sessionId": "s-1"})
    assert r.status_code == 204
    assert await _count(client, PortalEvent) == 1
    assert await _count(client, PortalVisit) == 1


@pytest.mark.requisito("RF-013")
async def test_unknown_site_key_is_rejected(client):
    r = await client.post("/events/track", json={"type": "pageview", "page": "/", "siteKey": "nope"})
    assert r.status_code == 403
    assert await _count(client, PortalEvent) == 0


@pytest.mark.requisito("RF-013")
async def test_disallowed_origin_is_rejected_and_allowed_origin_accepted(client):
    body = {"type": "pageview", "page": "/", "siteKey": SITE_KEY, "visitorId": "v-origin"}
    assert (await client.post("/events/track", json=body, headers={"Origin": "https://evil.example"})).status_code == 403
    assert (await client.post("/events/track", json=body, headers={"Origin": "https://www.cjhirashi.com"})).status_code == 204
    assert (await client.post("/events/track", json=body)).status_code == 204  # sin Origin no se puede imponer


@pytest.mark.requisito("RF-011")
async def test_internal_error_still_returns_204(client):
    with patch("routes.events.ingest_event", side_effect=RuntimeError("boom")):
        r = await client.post("/events/track", json={"type": "pageview", "page": "/"})
    assert r.status_code == 204


@pytest.mark.requisito("RF-013")
async def test_rate_limit_returns_429(client):
    with patch("routes.events._visitor_limiter", SlidingWindowLimiter(limit=2)):
        codes = [(await client.post("/events/track", json={"type": "pageview", "page": "/", "visitorId": "v-rate"})).status_code
                 for _ in range(3)]
    assert codes == [204, 204, 429]


@pytest.mark.requisito("RF-005")
async def test_ip_is_never_persisted(client):
    body = {"type": "pageview", "page": "/", "visitorId": "v-ip", "ip": "198.51.100.9", "siteKey": SITE_KEY}
    r = await client.post("/events/track", json=body, headers={"cf-connecting-ip": CLIENT_IP})
    assert r.status_code == 204
    async with client.test_db() as s:
        tables = (await s.execute(text("SELECT table_name FROM information_schema.tables WHERE table_name LIKE 'portal_%'"))).scalars().all()
        for table in tables:
            rows = (await s.execute(text(f"SELECT row_to_json(t)::text FROM {table} t"))).scalars().all()
            dump = "\n".join(rows)
            assert CLIENT_IP not in dump and "198.51.100.9" not in dump, table


@pytest.mark.requisito("RF-012")
async def test_forget_deletes_visitor_visits_and_events(client):
    for page in ("/", "/about"):
        await client.post("/events/track", json={"type": "pageview", "page": page, "siteKey": SITE_KEY, "visitorId": "v-forget"})
    await client.post("/events/track", json={"type": "pageview", "page": "/", "siteKey": SITE_KEY, "visitorId": "v-keep"})
    assert await _count(client, PortalVisitor) == 2

    r = await client.post("/events/forget", json={"siteKey": SITE_KEY, "visitorId": "v-forget"})
    assert r.status_code == 204
    async with client.test_db() as s:
        keys = (await s.execute(select(PortalVisitor.visitor_key))).scalars().all()
    assert keys == ["v-keep"]
    assert await _count(client, PortalVisit) == 1
    assert await _count(client, PortalEvent) == 1

    # Un visitante inexistente responde igual (no permite sondear ids).
    assert (await client.post("/events/forget", json={"siteKey": SITE_KEY, "visitorId": "nunca-existio"})).status_code == 204


def test_origin_allowed_rules():
    assert origin_allowed(None, ["cjhirashi.com"])
    assert origin_allowed("cjhirashi.com", ["cjhirashi.com"])
    assert origin_allowed("blog.cjhirashi.com", ["cjhirashi.com"])
    assert not origin_allowed("evil-cjhirashi.com", ["cjhirashi.com"])
    assert not origin_allowed("evil.example", ["cjhirashi.com"])
    assert origin_allowed("anything.example", [])


def test_sliding_window_limiter():
    limiter = SlidingWindowLimiter(limit=2, window=10)
    assert limiter.allow("k", now=0) and limiter.allow("k", now=1)
    assert not limiter.allow("k", now=2)
    assert limiter.allow("k", now=12)  # la ventana ya expiró
    assert limiter.allow("otro", now=2)
