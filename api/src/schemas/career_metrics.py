"""
Pydantic schemas - Career domain (v2) metrics.

Read-only response schema for `search_metrics_view`.
"""
from pydantic import BaseModel
from typing import Optional
from datetime import date


class SearchMetricsWeekResponse(BaseModel):
    """One row of the weekly search metrics view for a given user."""

    week_start: Optional[date] = None
    applications_sent: int = 0
    responses_received: int = 0
    response_rate_percentage: Optional[float] = None
    interviews_scheduled: int = 0
    offers: int = 0
    rejections: int = 0

    class Config:
        from_attributes = True
