"""Schemas del registro centralizado de fallas (ADR-018)."""
from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, Field


class ErrorReportIngest(BaseModel):
    """Cuerpo del endpoint público `POST /system/error-report`.

    Lo usan los SPA (Admin, Portfolio), que no tienen acceso a la base de datos.
    """

    message: str = Field(min_length=1, max_length=8000)
    source: str = Field(min_length=1, max_length=255)
    severity: str = Field(default="error", pattern="^(warning|error|critical)$")
    error_type: Optional[str] = Field(default=None, max_length=120)
    stack_trace: Optional[str] = Field(default=None, max_length=20000)
    context: Optional[dict[str, Any]] = None


class ErrorReportItem(BaseModel):
    id: str
    message: str
    source: str
    error_type: Optional[str] = None
    severity: str
    resolved: bool
    occurrences: int
    first_seen_at: Optional[str] = None
    last_seen_at: Optional[str] = None
    created_at: Optional[str] = None
    resolved_at: Optional[str] = None
    resolved_by: Optional[str] = None
    resolution_notes: Optional[str] = None


class ErrorReportDetail(ErrorReportItem):
    stack_trace: Optional[str] = None
    context: Optional[dict[str, Any]] = None


class ErrorReportList(BaseModel):
    items: List[ErrorReportItem]
    total: int
    page: int
    page_size: int
    has_more: bool


class ErrorReportUpdate(BaseModel):
    resolved: bool
    resolution_notes: Optional[str] = Field(default=None, max_length=8000)


class ErrorReportSummary(BaseModel):
    pending: int
    resolved: int
    by_severity: dict[str, int]
    newest_pending_at: Optional[str] = None


class PurgeResolvedRequest(BaseModel):
    older_than_days: int = Field(default=30, ge=0, le=3650)


class PurgeResolvedResponse(BaseModel):
    deleted: int
