"""Rellenado de la migración (A4): reconstruye visitantes y visitas desde eventos v1, con Postgres real."""
import hashlib
import importlib.util
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy import select

from config import settings
from models import PortalEvent, PortalSite, PortalVisit, PortalVisitor, User

MIGRATION = Path(__file__).resolve().parents[2] / "alembic" / "versions" / "b8d2f4a6c1e9_portal_analytics.py"
T0 = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)


def _load_migration():
    spec = importlib.util.spec_from_file_location("portal_analytics_migration", MIGRATION)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
async def legacy_data(db_session):
    db_session.add(User(id=settings.PUBLIC_PORTAL_USER_ID, username="legacy-owner", email="legacy@example.com",
                        password_hash="x", is_active=True))
    await db_session.flush()
    site = PortalSite(user_id=settings.PUBLIC_PORTAL_USER_ID, name="s", domain="cjhirashi.com", public_key="legacy-key",
                      owner_token_hash=hashlib.sha256(b"t").hexdigest(), allowed_hosts=["cjhirashi.com"], active=True)
    db_session.add(site)
    await db_session.flush()

    def event(session_id, minutes, page="/", event_type="pageview"):
        return PortalEvent(user_id=settings.PUBLIC_PORTAL_USER_ID, event_type=event_type, page=page,
                           session_id=session_id, created_at=T0 + timedelta(minutes=minutes), user_agent="Mozilla/5.0")

    # s-a: dos visitas (hueco de 3 h); s-b: una; sin sesión: un visitante por evento.
    db_session.add_all([event("s-a", 0), event("s-a", 5, "/proyectos"), event("s-a", 185, "/contacto"),
                        event("s-b", 60), event(None, 90)])
    await db_session.flush()

    conn = await db_session.connection()
    await conn.run_sync(lambda sync_conn: _load_migration()._backfill_legacy(sync_conn, settings.PUBLIC_PORTAL_USER_ID, site.id))
    return site


@pytest.mark.requisito("RF-040")
async def test_backfill_builds_visitors_and_visits_from_sessions(legacy_data, db_session):
    visitors = (await db_session.execute(select(PortalVisitor))).scalars().all()
    visits = (await db_session.execute(select(PortalVisit))).scalars().all()
    events = (await db_session.execute(select(PortalEvent))).scalars().all()

    assert len(visitors) == 3 and all(v.legacy for v in visitors)
    assert len(visits) == 4
    assert all(e.visit_id and e.visitor_id and e.site_id == legacy_data.id for e in events)
    assert {v.visitor_key: v.visit_count for v in visitors}["s-a"] == 2


@pytest.mark.requisito("RF-040")
async def test_backfill_marks_only_the_first_visit_of_each_visitor_as_new(legacy_data, db_session):
    visitor = (await db_session.execute(select(PortalVisitor).where(PortalVisitor.visitor_key == "s-a"))).scalar_one()
    visits = (await db_session.execute(
        select(PortalVisit).where(PortalVisit.visitor_id == visitor.id).order_by(PortalVisit.started_at)
    )).scalars().all()

    assert [v.is_new_visitor for v in visits] == [True, False]
    all_visits = (await db_session.execute(select(PortalVisit))).scalars().all()
    assert sum(v.is_new_visitor for v in all_visits) == 3  # una por visitante
