"""
Pydantic schemas - analítica del portafolio (SPEC-0010): respuestas de
/career/portal-metrics/*. Todas las respuestas agregadas traen `sample_size`
para que quien las lea (agente o tablero) sepa cuántas visitas las sustentan.
"""
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class Period(BaseModel):
    since: date
    until: date


class SampleSize(BaseModel):
    visits: int
    visitors: int


class Kpis(BaseModel):
    visitors: int
    visits: int
    pageviews: int
    pages_per_visit: Optional[float] = None
    bounce_rate: Optional[float] = None
    engagement_rate: Optional[float] = None
    median_active_ms: Optional[int] = None
    p90_active_ms: Optional[int] = None
    converted_visits: int
    converting_visitors: int
    conversion_rate: Optional[float] = None
    new_visitors: int
    returning_visitors: int


class KpiDelta(BaseModel):
    current: Optional[float] = None
    previous: Optional[float] = None
    delta_abs: Optional[float] = None
    delta_pct: Optional[float] = None


class KpisResponse(BaseModel):
    site_id: str
    period: Period
    sample_size: SampleSize
    kpis: Kpis
    compare: Optional[str] = None
    compare_period: Optional[Period] = None
    previous_kpis: Optional[Kpis] = None
    deltas: Optional[Dict[str, KpiDelta]] = None
    filters_applied: Dict[str, Any] = {}


class TrendPoint(BaseModel):
    bucket: date
    visits: int
    visitors: int
    pageviews: int
    engaged_visits: int
    # Solo con `compare`: el valor del mismo punto en el periodo comparado.
    previous_visits: Optional[int] = None


class TrendResponse(BaseModel):
    site_id: str
    period: Period
    granularity: str
    sample_size: SampleSize
    points: List[TrendPoint]
    annotations: List[Dict[str, Any]] = []
    # Último bucket aún en curso (el tablero lo dibuja punteado).
    incomplete_from: Optional[date] = None


class BreakdownRow(BaseModel):
    key: Optional[str] = None
    visitors: int
    visits: int
    pageviews: int
    share: float
    bounce_rate: Optional[float] = None
    median_active_ms: Optional[int] = None
    converted_visits: int


class BreakdownResponse(BaseModel):
    site_id: str
    period: Period
    dimension: str
    sample_size: SampleSize
    rows: List[BreakdownRow]


class PageRow(BaseModel):
    page: str
    pageviews: int
    visitors: int
    entries: int
    exits: int
    exit_rate: Optional[float] = None
    median_active_ms: Optional[int] = None
    avg_max_scroll_pct: Optional[float] = None


class PagesResponse(BaseModel):
    site_id: str
    period: Period
    sample_size: SampleSize
    rows: List[PageRow]


class PathRow(BaseModel):
    from_page: str
    to_page: str
    count: int


class PathsResponse(BaseModel):
    site_id: str
    period: Period
    sample_size: SampleSize
    rows: List[PathRow]


class RetentionRow(BaseModel):
    cohort_week: date
    size: int
    # Visitantes de la cohorte con visita n semanas después (índice 0 = su primera semana).
    active_by_week: List[int]


class RetentionResponse(BaseModel):
    site_id: str
    period: Period
    sample_size: SampleSize
    rows: List[RetentionRow]


class RealtimeResponse(BaseModel):
    site_id: str
    window_minutes: int
    visitors_now: int
    top_pages: List[Dict[str, Any]]
    generated_at: datetime


class GoalRow(BaseModel):
    goal_id: str
    name: str
    type: str
    is_key_event: bool
    converted_visits: int
    converting_visitors: int
    conversion_rate: Optional[float] = None


class GoalsResponse(BaseModel):
    site_id: str
    period: Period
    sample_size: SampleSize
    rows: List[GoalRow]


class FunnelStepRow(BaseModel):
    label: str
    visits: int
    from_previous: Optional[float] = None
    from_start: Optional[float] = None


class FunnelResponse(BaseModel):
    site_id: str
    funnel_id: str
    name: str
    period: Period
    sample_size: SampleSize
    steps: List[FunnelStepRow]


class RebuildResponse(BaseModel):
    site_id: str
    visits_recomputed: int = 0
    days_recomputed: int
    rows_written: int
