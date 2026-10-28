"""
Pydantic schema for the public, unauthenticated POST /events/track endpoint -
mirrors the portfolio frontend's `TrackingEvent` type exactly
(cjhirashi-career-portfolio/src/types/index.ts).
"""
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field

EventTypeLiteral = Literal["pageview", "click", "download", "form_submit", "scroll", "page_duration"]


class TrackEventIn(BaseModel):
    type: EventTypeLiteral
    page: str = Field(..., max_length=500)
    target: Optional[str] = Field(None, max_length=255)
    metadata: Optional[Dict[str, Any]] = None
    # Client-generated id for the current browser tab/session (sessionStorage
    # on the portfolio side) - groups pageviews into one visit server-side.
    sessionId: Optional[str] = Field(None, max_length=64)
    # Only sent with type="page_duration": milliseconds the visitor spent on
    # `page` before navigating away or closing the tab.
    durationMs: Optional[int] = Field(None, ge=0, le=86_400_000)
    # Client-reported timestamp/IP are informational only - never trusted for
    # storage. The server's own clock and the real request IP are used instead.
    timestamp: Optional[str] = None
    userAgent: Optional[str] = Field(None, max_length=500)
    ip: Optional[str] = None
