"""
Pydantic schemas - Career domain (v2) metrics.

Read-only response schemas: `SearchMetricsWeekResponse` for `search_metrics_view`,
and `SearchOverviewResponse` for the aggregated Operativa de Búsqueda dashboard
(counts/breakdowns computed live from the 12 search-domain tables, not stored).
"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import date


# ============================================================================
# Métricas semanales — respuestas
# ============================================================================

class SearchMetricsWeekResponse(BaseModel):
    """One row of the weekly search metrics view for a given user."""

    week_start: Optional[date] = None
    applications_sent: int = 0
    responses_received: int = 0
    response_rate_percentage: Optional[float] = None
    interviews_scheduled: int = 0
    offers: int = 0
    rejections: int = 0
    notes: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================================
# Componentes del dashboard — modelos auxiliares
# ============================================================================

class FunnelStage(BaseModel):
    label: str
    value: int


class CountBreakdown(BaseModel):
    label: str
    count: int


class MarketSegmentMetric(BaseModel):
    channel_name: Optional[str] = None
    market_type: Optional[str] = None
    priority: Optional[int] = None
    applications_made: int = 0
    responses_received: int = 0
    interviews_achieved: int = 0


class FitFactorMetric(BaseModel):
    factor_name: str
    weight_percentage: Optional[int] = None


class SearchPlanMetric(BaseModel):
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    plan_status: str
    completion_percentage: int = 0
    target_cvs_sent: int = 0
    target_interviews: int = 0
    target_offers: int = 0


# ============================================================================
# Vista general de búsqueda — respuesta agregada
# ============================================================================

class SearchOverviewResponse(BaseModel):
    """Aggregated snapshot across the 12 Operativa de Búsqueda tables, for the
    dashboard's charts - everything computed live per request, nothing here
    is stored on its own."""

    funnel: List[FunnelStage]
    vacancies_by_evaluation: List[CountBreakdown]
    vacancies_by_track: List[CountBreakdown]
    fit_percentage_avg: Optional[float] = None
    fit_percentage_min: Optional[int] = None
    fit_percentage_max: Optional[int] = None
    market_segments: List[MarketSegmentMetric]
    networking_by_status: List[CountBreakdown]
    networking_by_category: List[CountBreakdown]
    companies_by_tier: List[CountBreakdown]
    companies_by_status: List[CountBreakdown]
    fit_scoring_factors: List[FitFactorMetric]
    active_search_plan: Optional[SearchPlanMetric] = None
    notes: Optional[str] = None
