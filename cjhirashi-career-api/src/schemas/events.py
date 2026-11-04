"""
Pydantic schema for the public, unauthenticated POST /events/track endpoint -
mirrors the portfolio frontend's `TrackingEvent` type exactly
(cjhirashi-career-portfolio/src/types/index.ts).

Supports both v1 (legacy, without siteKey/visitorId) and v2 (new analytics).
"""
import re
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field, field_validator

EventTypeLiteral = Literal[
    "pageview",
    "click",
    "download",
    "form_submit",
    "scroll",
    "page_duration",
    "outbound",
    "project_open",
    "web_vitals",
    "page_leave",
]


class TrackEventIn(BaseModel):
    # --- Versión v1 (heredada, sigue siendo válida) ---
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

    # --- Versión v2 (nuevos campos opcionales) ---
    # Public key of the portal site (24 random chars)
    siteKey: Optional[str] = Field(None, max_length=32)
    # Persistent visitor ID (from client localStorage). Must match [A-Za-z0-9_-]+.
    visitorId: Optional[str] = Field(None, max_length=64)
    # Page title for SEO context
    title: Optional[str] = Field(None, max_length=500)
    # Target URL (for outbound links)
    targetUrl: Optional[str] = Field(None, max_length=1024)
    # Referrer URL (captures document.referrer)
    referrer: Optional[str] = Field(None, max_length=1024)
    # UTM parameters (dict). Only utm_source, utm_medium, utm_campaign,
    # utm_content, utm_term are preserved; others are discarded.
    utm: Optional[Dict[str, str]] = Field(None)
    # Click IDs. Only gclid, fbclid, msclkid, ttclid, twclid, li_fat_id are kept.
    clickIds: Optional[Dict[str, str]] = Field(None)
    # Max scroll percentage (0-100) on the page
    scrollPct: Optional[int] = Field(None, ge=0, le=100)
    # Active time in milliseconds (when page has focus and user is interacting)
    activeMs: Optional[int] = Field(None, ge=0, le=86_400_000)
    # Screen resolution string (e.g., "1920x1080")
    screen: Optional[str] = Field(None, max_length=20)
    # Owner token for marking self visits
    ownerToken: Optional[str] = Field(None, max_length=128)
    # Custom event properties
    props: Optional[Dict[str, Any]] = None
    # Web Vitals (LCP, INP, CLS, FCP, TTFB as floats)
    vitals: Optional[Dict[str, float]] = None

    @field_validator("visitorId")
    @classmethod
    def validate_visitor_id(cls, v):
        """visitorId must match [A-Za-z0-9_-]+ or be None."""
        if v is not None and not re.match(r"^[A-Za-z0-9_-]+$", v):
            raise ValueError("visitorId must contain only alphanumeric, underscore, and hyphen characters")
        return v

    @field_validator("utm", mode="before")
    @classmethod
    def filter_utm_params(cls, v):
        """Keep only allowed UTM keys and truncate values to 255 chars."""
        if v is None:
            return None
        allowed_keys = {"utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term"}
        filtered = {}
        for key, value in v.items():
            if key in allowed_keys:
                # Truncate value to 255 chars
                filtered[key] = str(value)[:255] if value else None
        return filtered if filtered else None

    @field_validator("clickIds", mode="before")
    @classmethod
    def filter_click_ids(cls, v):
        """Keep only allowed click ID keys."""
        if v is None:
            return None
        allowed_keys = {"gclid", "fbclid", "msclkid", "ttclid", "twclid", "li_fat_id"}
        filtered = {}
        for key, value in v.items():
            if key in allowed_keys:
                filtered[key] = value
        return filtered if filtered else None

    @field_validator("vitals", mode="before")
    @classmethod
    def filter_vitals(cls, v):
        """Keep only allowed vitals keys."""
        if v is None:
            return None
        allowed_keys = {"lcp", "inp", "cls", "fcp", "ttfb"}
        filtered = {}
        for key, value in v.items():
            if key in allowed_keys:
                try:
                    filtered[key] = float(value)
                except (TypeError, ValueError):
                    pass
        return filtered if filtered else None
