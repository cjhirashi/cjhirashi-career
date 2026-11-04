"""Rutas /career/portal-metrics/* (SPEC-0010 D3-D7): contrato, parámetros y errores."""
import pytest
from httpx import ASGITransport, AsyncClient

from app import app
from config import settings
from database import get_db
from middleware.auth import get_current_user
from models import User
from tests.unit.test_portal_metrics_engine import seeded  # noqa: F401  (fixture de datos sintéticos)

BASE = "/career/portal-metrics"
WINDOW = {"since": "2026-10-01", "until": "2026-10-03"}


@pytest.fixture
async def api(db_session, seeded):  # noqa: F811
    site, funnel = seeded
    user = (await db_session.get(User, settings.PUBLIC_PORTAL_USER_ID))

    async def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: user
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        client.site, client.funnel = site, funnel
        yield client
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


LEGACY_KEYS = {"total_pageviews", "pageviews_in_window", "total_visits", "visits_in_window", "window_days",
               "visits_by_day", "visits_by_country", "visits_by_location", "top_pages", "duration_ms_min",
               "duration_ms_avg", "duration_ms_max", "duration_sample_size"}


@pytest.mark.requisito("RF-032")
async def test_overview_keeps_legacy_contract_and_adds_new_fields(api):
    r = await api.get(f"{BASE}/overview", params=WINDOW)
    assert r.status_code == 200
    body = r.json()
    assert LEGACY_KEYS <= set(body)
    assert body["visits_in_window"] == 5 and body["pageviews_in_window"] == 6 and body["window_days"] == 3
    assert body["sample_size"] == {"visits": 5, "visitors": 4}
    assert body["kpis"]["bounce_rate"] == 0.6 and body["site_id"] == api.site.id
    assert {c["label"] for c in body["visits_by_country"]} == {"Mexico", "Spain"}
    assert body["top_pages"][0] == {"label": "/", "count": 3}
    assert [d["count"] for d in body["visits_by_day"]] == [3, 2, 0]
    assert body["duration_ms_max"] == 20000 and body["duration_ms_median"] is not None


@pytest.mark.requisito("RF-032")
async def test_overview_flags_and_compare(api):
    all_traffic = (await api.get(f"{BASE}/overview", params={**WINDOW, "exclude_bots": "false", "exclude_owner": "false"})).json()
    assert all_traffic["visits_in_window"] == 7
    r = (await api.get(f"{BASE}/overview", params={"since": "2026-10-08", "until": "2026-10-08", "compare": "previous"})).json()
    assert r["kpis"]["visits"] == 1 and r["previous_kpis"]["visits"] == 0  # el 8 hay una visita (V7); el 7 ninguna
    cmp_ = (await api.get(f"{BASE}/overview", params={**WINDOW, "compare": "weekday"})).json()
    assert cmp_["compare"] == "weekday" and cmp_["deltas"]["visits"]["previous"] == 0


@pytest.mark.requisito("RF-034")
async def test_kpis_compare_period_and_deltas(api):
    r = (await api.get(f"{BASE}/kpis", params={"since": "2026-10-04", "until": "2026-10-10", "compare": "previous"})).json()
    assert r["compare_period"] == {"since": "2026-09-27", "until": "2026-10-03"}
    assert r["kpis"]["visits"] == 1 and r["previous_kpis"]["visits"] == 5
    assert r["deltas"]["visits"]["delta_abs"] == -4 and r["deltas"]["visits"]["delta_pct"] == -0.8
    assert r["sample_size"] == {"visits": 1, "visitors": 1}


@pytest.mark.requisito("RF-037")
async def test_every_aggregate_reports_sample_size(api):
    for path in ("kpis", "trend", "channels", "sources", "campaigns", "geo", "devices", "pages", "paths", "retention", "goals"):
        r = await api.get(f"{BASE}/{path}", params=WINDOW)
        assert r.status_code == 200, path
        assert r.json()["sample_size"] == {"visits": 5, "visitors": 4}, path
    r = await api.get(f"{BASE}/funnel/{api.funnel.id}", params=WINDOW)
    assert r.status_code == 200 and r.json()["sample_size"]["visits"] == 5


@pytest.mark.requisito("RF-033")
async def test_breakdown_geo_devices_and_filters(api):
    geo = (await api.get(f"{BASE}/geo", params={**WINDOW, "level": "country"})).json()
    assert {r["key"]: r["visits"] for r in geo["rows"]} == {"Mexico": 4, "Spain": 1}
    devices = (await api.get(f"{BASE}/devices", params={**WINDOW, "by": "device_type"})).json()
    assert {r["key"]: r["visits"] for r in devices["rows"]} == {"desktop": 4, "mobile": 1}
    filtered = (await api.get(f"{BASE}/channels", params={**WINDOW, "filters": '{"country": "Spain"}'})).json()
    assert [r["key"] for r in filtered["rows"]] == ["Referral"]
    assert (await api.get(f"{BASE}/breakdown", params={**WINDOW, "dimension": "utm_campaign"})).status_code == 200


@pytest.mark.requisito("RF-033")
async def test_trend_marks_incomplete_period_and_annotations(api):
    body = (await api.get(f"{BASE}/trend", params={**WINDOW, "compare": "previous"})).json()
    assert body["incomplete_from"] is None  # ventana pasada: no hay periodo en curso
    assert [p["visits"] for p in body["points"]] == [3, 2, 0]
    assert [p["previous_visits"] for p in body["points"]] == [0, 0, 0]
    weekly = (await api.get(f"{BASE}/trend", params={**WINDOW, "granularity": "week"})).json()
    assert sum(p["visits"] for p in weekly["points"]) == 5


@pytest.mark.requisito("RF-033")
async def test_realtime_dictionary_and_rebuild(api):
    assert (await api.get(f"{BASE}/realtime")).json()["visitors_now"] == 0
    dictionary = (await api.get(f"{BASE}/dictionary")).json()
    assert "engaged_visit" in dictionary["definitions"] and "channel" in dictionary["filters"]
    rebuilt = await api.post(f"{BASE}/rebuild", params=WINDOW)
    assert rebuilt.status_code == 200 and rebuilt.json()["rows_written"] > 0


@pytest.mark.requisito("RF-033")
async def test_invalid_parameters_return_400_and_missing_funnel_404(api):
    assert (await api.get(f"{BASE}/kpis", params={**WINDOW, "filters": '{"nope": 1}'})).status_code == 400
    assert (await api.get(f"{BASE}/kpis", params={**WINDOW, "filters": "no-es-json"})).status_code == 400
    assert (await api.get(f"{BASE}/kpis", params={**WINDOW, "compare": "mañana"})).status_code == 400
    assert (await api.get(f"{BASE}/kpis", params={"since": "2026-10-05", "until": "2026-10-01"})).status_code == 400
    assert (await api.get(f"{BASE}/breakdown", params={**WINDOW, "dimension": "password"})).status_code == 400
    assert (await api.get(f"{BASE}/trend", params={**WINDOW, "granularity": "hour"})).status_code == 400
    assert (await api.get(f"{BASE}/funnel/pfn-9999", params=WINDOW)).status_code == 404
    assert (await api.get(f"{BASE}/kpis", params={**WINDOW, "site_id": "psi-9999"})).status_code == 404
