"""
Career domain (v2) - Portal analytics (Presencia Digital), SPEC-0010.

Read-only aggregation over `portal_visits` / `portal_events` / `portal_daily`
(captured by the public POST /events/track endpoint, see routes/events.py).
Every endpoint shares the same parameters (see `_common`) and the same filter
builder (services/portal_metrics.MetricsQuery), so clean traffic (no bots, no
owner visits) is the default everywhere and every aggregate reports its
`sample_size`.
"""
import json
from datetime import date, datetime, timedelta
from typing import Any, Dict, Optional
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from middleware.auth import get_current_user
from models.portal_event import PortalEvent
from models.portal_funnel import PortalFunnel
from models.portal_visit import PortalVisit
from models.user import User
from schemas.career_metrics import CountBreakdown
from schemas.portal_analytics_metrics import (
    BreakdownResponse, FunnelResponse, GoalsResponse, KpisResponse, PagesResponse, PathsResponse,
    RealtimeResponse, RebuildResponse, RetentionResponse, TrendResponse,
)
from schemas.portal_metrics import DailyCount, LocationCount, PortalMetricsOverviewResponse
from services import portal_metrics as pm

router = APIRouter(prefix="/career/portal-metrics", tags=["Career - Portal Metrics"])

BREAKDOWN_ALIASES = {
    "channels": "channel",
    "sources": "source",
    "campaigns": "utm_campaign",
}


async def _common(
    site_id: Optional[str] = Query(None, description="Sitio medido; por defecto el primero activo del dueño"),
    since: Optional[date] = Query(None, description="Inicio (fecha en la zona del sitio); por defecto until - days + 1"),
    until: Optional[date] = Query(None, description="Fin inclusive; por defecto hoy en la zona del sitio"),
    days: int = Query(30, ge=1, le=3650, description="Largo de la ventana si no se da `since`"),
    exclude_bots: bool = Query(True, description="Excluir visitas marcadas como bot"),
    exclude_owner: bool = Query(True, description="Excluir las visitas del propio dueño"),
    filters: Optional[str] = Query(None, description='JSON {"channel":"Organic Social","country":["Mexico"]}. Claves: ver /dictionary'),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> pm.MetricsQuery:
    site = await pm.resolve_site(db, current_user.id, site_id)
    if site is None:
        raise HTTPException(status_code=404, detail="No hay un sitio de analítica configurado")
    parsed: Dict[str, Any] = {}
    if filters:
        try:
            parsed = json.loads(filters)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail="filters debe ser un objeto JSON") from exc
        if not isinstance(parsed, dict):
            raise HTTPException(status_code=400, detail="filters debe ser un objeto JSON")
        unknown = [k for k in parsed if k not in pm.FILTERABLE]
        if unknown:
            raise HTTPException(status_code=400, detail=f"Filtros desconocidos: {', '.join(unknown)}")
    end = until or datetime.now(ZoneInfo(site.timezone or "America/Mexico_City")).date()
    start = since or end - timedelta(days=days - 1)
    if start > end:
        raise HTTPException(status_code=400, detail="since no puede ser posterior a until")
    return pm.MetricsQuery(current_user.id, site, start, end, exclude_bots, exclude_owner, parsed)


def _period(q: pm.MetricsQuery) -> dict:
    return {"since": q.since, "until": q.until}


def _bad_request(exc: ValueError) -> HTTPException:
    return HTTPException(status_code=400, detail=str(exc))


@router.get("/dictionary")
async def get_dictionary(current_user: User = Depends(get_current_user)):
    """Definiciones de cada métrica y de los filtros disponibles."""
    return {"definitions": pm.DICTIONARY, "filters": sorted(pm.FILTERABLE), "compare": ["none", "previous", "year", "weekday"]}


@router.get("/overview", response_model=PortalMetricsOverviewResponse)
async def get_portal_metrics_overview(
    compare: str = Query("none", description="none | previous | year | weekday"),
    q: pm.MetricsQuery = Depends(_common),
    db: AsyncSession = Depends(get_db),
):
    """Resumen general. Conserva los campos históricos (`total_*`, `visits_by_*`, `top_pages`,
    `duration_ms_*`) y añade `kpis`, `sample_size`, mediana y p90 de duración y comparación."""
    all_time = q.shifted(date(2000, 1, 1), q.until)
    totals = await pm.kpis(db, all_time)
    current = await pm.kpis(db, q)

    trend_points = await pm.trend(db, q, "day")
    countries = await pm.breakdown(db, q, "country", limit=20)
    pages = await pm.pages(db, q, limit=20)

    location_rows = (
        await db.execute(
            select(PortalVisit.city, PortalVisit.country, func.avg(PortalVisit.latitude), func.avg(PortalVisit.longitude), func.count())
            .where(*q.visit_conditions(), PortalVisit.latitude.is_not(None), PortalVisit.longitude.is_not(None))
            .group_by(PortalVisit.city, PortalVisit.country)
            .order_by(func.count().desc())
            .limit(200)
        )
    ).all()

    e = PortalEvent
    seconds = func.least(func.coalesce(e.active_ms, e.duration_ms), pm.MAX_ACTIVE_MS)
    duration = (
        await db.execute(
            select(func.min(seconds), func.avg(seconds), func.max(seconds), func.count(),
                   func.percentile_cont(0.5).within_group(seconds), func.percentile_cont(0.9).within_group(seconds))
            .where(e.visit_id.in_(q.visit_ids()), e.event_type.in_(["page_duration", "page_leave"]),
                   func.coalesce(e.active_ms, e.duration_ms).is_not(None))
        )
    ).one()

    response: Dict[str, Any] = {
        "total_pageviews": totals["pageviews"],
        "pageviews_in_window": current["pageviews"],
        "total_visits": totals["visits"],
        "visits_in_window": current["visits"],
        "window_days": q.days,
        "visits_by_day": [DailyCount(day=p["bucket"], count=p["visits"]) for p in trend_points],
        "visits_by_country": [CountBreakdown(label=r["key"] or "Desconocido", count=r["visits"]) for r in countries],
        "visits_by_location": [
            LocationCount(city=city, country=country, latitude=lat, longitude=lng, count=count)
            for city, country, lat, lng, count in location_rows
        ],
        "top_pages": [CountBreakdown(label=r["page"], count=r["pageviews"]) for r in pages],
        "duration_ms_min": pm._int(duration[0]),
        "duration_ms_avg": pm._int(duration[1]),
        "duration_ms_max": pm._int(duration[2]),
        "duration_sample_size": duration[3],
        "duration_ms_median": pm._int(duration[4]),
        "duration_ms_p90": pm._int(duration[5]),
        "site_id": q.site.id,
        "sample_size": {"visits": current["visits"], "visitors": current["visitors"]},
        "kpis": current,
    }
    try:
        window = pm.compare_period(q, compare)
    except ValueError as exc:
        raise _bad_request(exc)
    if window:
        previous = await pm.kpis(db, q.shifted(*window))
        response.update(compare=compare, previous_kpis=previous, deltas=pm.deltas(current, previous))
    return response


@router.get("/kpis", response_model=KpisResponse)
async def get_kpis(
    compare: str = Query("none", description="none | previous | year | weekday"),
    q: pm.MetricsQuery = Depends(_common),
    db: AsyncSession = Depends(get_db),
):
    current = await pm.kpis(db, q)
    body: Dict[str, Any] = {
        "site_id": q.site.id, "period": _period(q), "sample_size": await pm.sample_size(db, q),
        "kpis": current, "filters_applied": q.filters,
    }
    try:
        window = pm.compare_period(q, compare)
    except ValueError as exc:
        raise _bad_request(exc)
    if window:
        previous = await pm.kpis(db, q.shifted(*window))
        body.update(compare=compare, compare_period={"since": window[0], "until": window[1]},
                    previous_kpis=previous, deltas=pm.deltas(current, previous))
    return body


@router.get("/trend", response_model=TrendResponse)
async def get_trend(
    granularity: str = Query("day", description="day | week | month"),
    compare: str = Query("none", description="none | previous | year | weekday (solo con granularity=day)"),
    q: pm.MetricsQuery = Depends(_common),
    db: AsyncSession = Depends(get_db),
):
    try:
        points = await pm.trend(db, q, granularity)
        window = pm.compare_period(q, compare)
    except ValueError as exc:
        raise _bad_request(exc)
    if window and granularity == "day":
        previous = await pm.trend(db, q.shifted(*window), "day")
        for point, before in zip(points, previous):
            point["previous_visits"] = before["visits"]
    today = datetime.now(q.tz).date()
    return {
        "site_id": q.site.id, "period": _period(q), "granularity": granularity,
        "sample_size": await pm.sample_size(db, q), "points": points,
        "annotations": await pm.annotations(db, q),
        "incomplete_from": today if q.since <= today <= q.until else None,
    }


async def _breakdown(db: AsyncSession, q: pm.MetricsQuery, dimension: str, limit: int) -> Dict[str, Any]:
    try:
        rows = await pm.breakdown(db, q, dimension, limit)
    except ValueError as exc:
        raise _bad_request(exc)
    return {"site_id": q.site.id, "period": _period(q), "dimension": dimension,
            "sample_size": await pm.sample_size(db, q), "rows": rows}


@router.get("/breakdown", response_model=BreakdownResponse)
async def get_breakdown(
    dimension: str = Query(..., description="Cualquier clave de filtro: channel, source, country, device_type, browser, os, utm_campaign, entry_page..."),
    limit: int = Query(50, ge=1, le=200),
    q: pm.MetricsQuery = Depends(_common),
    db: AsyncSession = Depends(get_db),
):
    return await _breakdown(db, q, dimension, limit)


@router.get("/channels", response_model=BreakdownResponse)
async def get_channels(limit: int = Query(50, ge=1, le=200), q: pm.MetricsQuery = Depends(_common), db: AsyncSession = Depends(get_db)):
    return await _breakdown(db, q, "channel", limit)


@router.get("/sources", response_model=BreakdownResponse)
async def get_sources(limit: int = Query(50, ge=1, le=200), q: pm.MetricsQuery = Depends(_common), db: AsyncSession = Depends(get_db)):
    return await _breakdown(db, q, "source", limit)


@router.get("/campaigns", response_model=BreakdownResponse)
async def get_campaigns(limit: int = Query(50, ge=1, le=200), q: pm.MetricsQuery = Depends(_common), db: AsyncSession = Depends(get_db)):
    """Visitas por `utm_campaign`; cruza con `application_id` en /career/portal-visits."""
    return await _breakdown(db, q, "utm_campaign", limit)


@router.get("/geo", response_model=BreakdownResponse)
async def get_geo(
    level: str = Query("country", pattern="^(country|region|city)$"),
    limit: int = Query(50, ge=1, le=200),
    q: pm.MetricsQuery = Depends(_common),
    db: AsyncSession = Depends(get_db),
):
    return await _breakdown(db, q, level, limit)


@router.get("/devices", response_model=BreakdownResponse)
async def get_devices(
    by: str = Query("device_type", pattern="^(device_type|browser|os|language)$"),
    limit: int = Query(50, ge=1, le=200),
    q: pm.MetricsQuery = Depends(_common),
    db: AsyncSession = Depends(get_db),
):
    return await _breakdown(db, q, by, limit)


@router.get("/pages", response_model=PagesResponse)
async def get_pages(limit: int = Query(50, ge=1, le=200), q: pm.MetricsQuery = Depends(_common), db: AsyncSession = Depends(get_db)):
    return {"site_id": q.site.id, "period": _period(q), "sample_size": await pm.sample_size(db, q),
            "rows": await pm.pages(db, q, limit)}


@router.get("/paths", response_model=PathsResponse)
async def get_paths(limit: int = Query(30, ge=1, le=100), q: pm.MetricsQuery = Depends(_common), db: AsyncSession = Depends(get_db)):
    return {"site_id": q.site.id, "period": _period(q), "sample_size": await pm.sample_size(db, q),
            "rows": await pm.paths(db, q, limit)}


@router.get("/retention", response_model=RetentionResponse)
async def get_retention(weeks: int = Query(4, ge=1, le=12), q: pm.MetricsQuery = Depends(_common), db: AsyncSession = Depends(get_db)):
    """Cohortes semanales de visitantes nuevos y cuántos regresan en las semanas siguientes."""
    return {"site_id": q.site.id, "period": _period(q), "sample_size": await pm.sample_size(db, q),
            "rows": await pm.retention(db, q, weeks)}


@router.get("/realtime", response_model=RealtimeResponse)
async def get_realtime(
    site_id: Optional[str] = Query(None),
    minutes: int = Query(5, ge=1, le=60),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    site = await pm.resolve_site(db, current_user.id, site_id)
    if site is None:
        raise HTTPException(status_code=404, detail="No hay un sitio de analítica configurado")
    return await pm.realtime(db, current_user.id, site, minutes)


@router.get("/goals", response_model=GoalsResponse)
async def get_goals(q: pm.MetricsQuery = Depends(_common), db: AsyncSession = Depends(get_db)):
    return {"site_id": q.site.id, "period": _period(q), "sample_size": await pm.sample_size(db, q),
            "rows": await pm.goals(db, q)}


@router.get("/funnel/{funnel_id}", response_model=FunnelResponse)
async def get_funnel(funnel_id: str, q: pm.MetricsQuery = Depends(_common), db: AsyncSession = Depends(get_db)):
    definition = (
        await db.execute(select(PortalFunnel).where(PortalFunnel.id == funnel_id, PortalFunnel.user_id == q.user_id,
                                                    PortalFunnel.site_id == q.site.id))
    ).scalar_one_or_none()
    if definition is None:
        raise HTTPException(status_code=404, detail="Embudo no encontrado")
    try:
        steps = await pm.funnel(db, q, definition)
    except ValueError as exc:
        raise _bad_request(exc)
    return {"site_id": q.site.id, "funnel_id": definition.id, "name": definition.name, "period": _period(q),
            "sample_size": await pm.sample_size(db, q), "steps": steps}


@router.post("/rebuild", response_model=RebuildResponse)
async def rebuild(
    include_visits: bool = Query(False, description="Recalcular también las visitas (canal, contadores, banderas) desde los eventos"),
    q: pm.MetricsQuery = Depends(_common),
    db: AsyncSession = Depends(get_db),
):
    """Recalcula lo derivado del rango desde el crudo: `portal_daily` y, con `include_visits`,
    las visitas (por ejemplo tras cambiar las reglas de canal). No modifica ni pierde eventos."""
    visits = await pm.rebuild_visits(db, q.user_id, q.site, q.since, q.until) if include_visits else 0
    result = await pm.rebuild_daily(db, q.user_id, q.site, q.since, q.until)
    await db.commit()
    return {"site_id": q.site.id, "visits_recomputed": visits, **result}
