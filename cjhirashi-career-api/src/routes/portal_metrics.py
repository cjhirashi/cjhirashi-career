"""
Career domain (v2) - Portal traffic metrics (Presencia Digital).

Read-only aggregation over `portal_events` (captured by the public
POST /events/track endpoint, see routes/events.py): pageviews over time,
visits by country, and the most-visited pages. Computed live per request,
same approach as career_metrics.search-overview.
"""
from datetime import date, timedelta
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from middleware.auth import get_current_user
from models.user import User
from models.portal_event import PortalEvent
from schemas.career_metrics import CountBreakdown
from schemas.portal_metrics import DailyCount, LocationCount, PortalMetricsOverviewResponse

router = APIRouter(prefix="/career/portal-metrics", tags=["Career - Portal Metrics"])


@router.get("/overview", response_model=PortalMetricsOverviewResponse)
async def get_portal_metrics_overview(
    days: int = Query(30, ge=1, le=365, description="Window for the daily trend"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = current_user.id
    since = date.today() - timedelta(days=days)
    pageview_filter = (PortalEvent.user_id == user_id, PortalEvent.event_type == "pageview")

    total_pageviews = (
        await db.execute(select(func.count()).select_from(PortalEvent).where(*pageview_filter))
    ).scalar_one()
    # Unique visits = distinct browser sessions, not raw pageview events (a
    # visitor opening 5 pages in one session is 1 visit, not 5). Events from
    # before `session_id` existed have none and COUNT(DISTINCT ...) ignores
    # NULLs, so they're excluded here rather than undercounting as "1".
    total_visits = (
        await db.execute(select(func.count(func.distinct(PortalEvent.session_id))).where(*pageview_filter))
    ).scalar_one()

    day_col = func.date(PortalEvent.created_at)
    visits_by_day_rows = (
        await db.execute(
            select(day_col.label("day"), func.count(func.distinct(PortalEvent.session_id)))
            .where(*pageview_filter, PortalEvent.created_at >= since)
            .group_by(day_col)
            .order_by(day_col)
        )
    ).all()
    visits_by_day: List[DailyCount] = [DailyCount(day=day, count=count) for day, count in visits_by_day_rows]
    visits_in_window = sum(d.count for d in visits_by_day)

    pageviews_in_window = (
        await db.execute(
            select(func.count()).select_from(PortalEvent).where(*pageview_filter, PortalEvent.created_at >= since)
        )
    ).scalar_one()

    country_rows = (
        await db.execute(
            select(PortalEvent.country, func.count())
            .where(*pageview_filter)
            .group_by(PortalEvent.country)
            .order_by(func.count().desc())
            .limit(20)
        )
    ).all()
    visits_by_country = [
        CountBreakdown(label=country or "Desconocido", count=count) for country, count in country_rows
    ]

    location_rows = (
        await db.execute(
            select(
                PortalEvent.city,
                PortalEvent.country,
                func.avg(PortalEvent.latitude),
                func.avg(PortalEvent.longitude),
                func.count(),
            )
            .where(*pageview_filter, PortalEvent.latitude.is_not(None), PortalEvent.longitude.is_not(None))
            .group_by(PortalEvent.city, PortalEvent.country)
            .order_by(func.count().desc())
            .limit(200)
        )
    ).all()
    visits_by_location = [
        LocationCount(city=city, country=country, latitude=lat, longitude=lng, count=count)
        for city, country, lat, lng, count in location_rows
    ]

    page_rows = (
        await db.execute(
            select(PortalEvent.page, func.count())
            .where(*pageview_filter)
            .group_by(PortalEvent.page)
            .order_by(func.count().desc())
            .limit(20)
        )
    ).all()
    top_pages = [CountBreakdown(label=page, count=count) for page, count in page_rows]

    # Time on page: one `page_duration` event per page visit (sendBeacon on
    # route change / tab close, see routes/events.py). A tab left open for
    # hours before `pagehide` fires would otherwise blow out the max, so the
    # same 24h sanity cap already enforced at ingestion (schemas/events.py)
    # is the only filtering needed here.
    duration_filter = (
        PortalEvent.user_id == user_id,
        PortalEvent.event_type == "page_duration",
        PortalEvent.created_at >= since,
        PortalEvent.duration_ms.is_not(None),
    )
    duration_stats = (
        await db.execute(
            select(
                func.min(PortalEvent.duration_ms),
                func.avg(PortalEvent.duration_ms),
                func.max(PortalEvent.duration_ms),
                func.count(),
            ).where(*duration_filter)
        )
    ).one()
    duration_min_ms, duration_avg_ms, duration_max_ms, duration_sample_size = duration_stats

    return PortalMetricsOverviewResponse(
        duration_ms_min=duration_min_ms,
        duration_ms_avg=round(float(duration_avg_ms)) if duration_avg_ms is not None else None,
        duration_ms_max=duration_max_ms,
        duration_sample_size=duration_sample_size,
        total_pageviews=total_pageviews,
        pageviews_in_window=pageviews_in_window,
        total_visits=total_visits,
        visits_in_window=visits_in_window,
        window_days=days,
        visits_by_day=visits_by_day,
        visits_by_country=visits_by_country,
        visits_by_location=visits_by_location,
        top_pages=top_pages,
    )
