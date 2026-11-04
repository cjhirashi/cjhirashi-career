"""
Pydantic schemas - Career domain (v2), Presencia Digital: portal traffic
metrics (GET /career/portal-metrics/overview). Everything computed live from
`portal_events`, nothing stored here on its own.
"""
from datetime import date
from typing import List, Optional

from pydantic import BaseModel

from schemas.career_metrics import CountBreakdown


class DailyCount(BaseModel):
    day: date
    count: int


class LocationCount(BaseModel):
    """One bubble on the traffic map - city+country with its averaged
    coordinates (Cloudflare reports slightly different coordinates for visitors
    in the same city, so they are averaged)."""

    city: Optional[str]
    country: Optional[str]
    latitude: float
    longitude: float
    count: int


class PortalMetricsOverviewResponse(BaseModel):
    total_pageviews: int
    pageviews_in_window: int
    # Unique visits = distinct browser sessions (`portal_events.session_id`),
    # not raw pageview events - several pages viewed in one visit count once.
    # Events captured before `session_id` existed have none and are excluded.
    total_visits: int
    visits_in_window: int
    window_days: int
    visits_by_day: List[DailyCount]
    visits_by_country: List[CountBreakdown]
    visits_by_location: List[LocationCount]
    top_pages: List[CountBreakdown]
    # Time on page within the window, in milliseconds - one sample per page
    # visit (`page_duration` events, see routes/events.py). None when there
    # isn't a single sample yet (e.g. right after deploying this feature).
    duration_ms_min: Optional[int] = None
    duration_ms_avg: Optional[int] = None
    duration_ms_max: Optional[int] = None
    duration_sample_size: int = 0
    # SPEC-0010: mediana y p90 (el promedio se distorsiona con pestañas olvidadas),
    # tamaño de muestra y el resumen de KPIs; se agregan sin tocar los campos anteriores.
    duration_ms_median: Optional[int] = None
    duration_ms_p90: Optional[int] = None
    site_id: Optional[str] = None
    sample_size: Optional[dict] = None
    kpis: Optional[dict] = None
    compare: Optional[str] = None
    previous_kpis: Optional[dict] = None
    deltas: Optional[dict] = None
