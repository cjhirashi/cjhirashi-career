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
    coordinates (ipapi.co resolves roughly the same point per city, but
    different visitors there can land on slightly different values)."""

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
