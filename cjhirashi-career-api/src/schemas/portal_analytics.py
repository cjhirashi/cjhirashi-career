"""
Pydantic schemas for portal analytics - read-only resources and CRUD configs.

D1 - Read-only analytics tables:
- PortalSiteOut (omits public_key and owner_token_hash)
- PortalVisitorOut
- PortalVisitOut
- PortalEventOut
- PortalDailyOut

D2 - Configuration CRUD:
- PortalGoal (Create/Update/Out)
- PortalFunnel (Create/Update/Out)
- PortalAnnotation (Create/Update/Out)
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime, date


# ============================================================================
# D1 — Read-only schemas (analytics tables)
# ============================================================================

class PortalSiteOut(BaseModel):
    """Portal site - omits public_key and owner_token_hash for security."""
    id: str
    user_id: str
    name: str
    domain: str
    allowed_hosts: Optional[List[Any]] = None
    timezone: str
    active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PortalVisitorOut(BaseModel):
    """Anonymous visitor with first/last seen, visit count, detection flags."""
    id: str
    user_id: str
    site_id: str
    visitor_key: str
    first_seen: datetime
    last_seen: datetime
    visit_count: int
    first_referrer_domain: Optional[str] = None
    first_channel: Optional[str] = None
    first_utm_source: Optional[str] = None
    first_utm_medium: Optional[str] = None
    first_utm_campaign: Optional[str] = None
    country: Optional[str] = None
    is_bot: bool
    bot_score: int
    is_owner: bool
    legacy: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PortalVisitOut(BaseModel):
    """One visit session with entry/exit, device, geography, engagement."""
    id: str
    user_id: str
    site_id: str
    visitor_id: str
    started_at: datetime
    last_activity_at: datetime
    entry_page: str
    exit_page: Optional[str] = None
    referrer_url: Optional[str] = None
    referrer_domain: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_content: Optional[str] = None
    utm_term: Optional[str] = None
    click_id_type: Optional[str] = None
    channel: Optional[str] = None
    source: Optional[str] = None
    device_type: Optional[str] = None
    browser: Optional[str] = None
    browser_version: Optional[str] = None
    os: Optional[str] = None
    os_version: Optional[str] = None
    screen_size: Optional[str] = None
    language: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None
    is_bot: bool
    bot_score: int
    bot_reasons: Optional[List[Any]] = None
    is_owner: bool
    is_new_visitor: bool
    pageviews: int
    events_count: int
    active_ms: int
    max_scroll_pct: int
    is_engaged: bool
    is_bounce: bool
    converted: bool
    application_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PortalEventOut(BaseModel):
    """One pageview/click/download event from an anonymous visitor."""
    id: str
    user_id: str
    event_type: str
    page: str
    target: Optional[str] = None
    session_id: Optional[str] = None
    duration_ms: Optional[int] = None
    event_metadata: Optional[Dict[str, Any]] = None
    country: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    user_agent: Optional[str] = None
    site_id: Optional[str] = None
    visitor_id: Optional[str] = None
    visit_id: Optional[str] = None
    seq: Optional[int] = None
    page_title: Optional[str] = None
    props: Optional[Dict[str, Any]] = None
    scroll_pct: Optional[int] = None
    active_ms: Optional[int] = None
    target_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PortalDailyOut(BaseModel):
    """Daily rollup of portal analytics by dimension."""
    id: str
    user_id: str
    site_id: str
    day: date
    dimension: str
    key: str
    visitors: int
    visits: int
    pageviews: int
    engaged_visits: int
    bounces: int
    active_ms_sum: int
    conversions: int
    computed_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# D2 — Configuration CRUD schemas (goals, funnels, annotations)
# ============================================================================

# ---- PortalGoal ----

class PortalGoalBase(BaseModel):
    name: str = Field(..., max_length=255)
    type: Literal["event", "page", "outbound", "min_active", "min_pages"]
    match: Dict[str, Any]
    is_key_event: bool = False


class PortalGoalCreate(PortalGoalBase):
    site_id: str  # Obligatorio al crear


class PortalGoalUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    type: Optional[Literal["event", "page", "outbound", "min_active", "min_pages"]] = None
    match: Optional[Dict[str, Any]] = None
    is_key_event: Optional[bool] = None


class PortalGoalOut(PortalGoalBase):
    id: str
    user_id: str
    site_id: str
    created_at: datetime

    class Config:
        from_attributes = True


# ---- PortalFunnel ----

class PortalFunnelStep(BaseModel):
    label: str
    type: Literal["event", "page", "outbound"]
    match: Dict[str, Any]


class PortalFunnelBase(BaseModel):
    name: str = Field(..., max_length=255)
    steps: List[PortalFunnelStep] = Field(..., min_length=2)


class PortalFunnelCreate(PortalFunnelBase):
    site_id: str  # Obligatorio al crear


class PortalFunnelUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    steps: Optional[List[PortalFunnelStep]] = Field(None, min_length=2)


class PortalFunnelOut(PortalFunnelBase):
    id: str
    user_id: str
    site_id: str
    created_at: datetime

    class Config:
        from_attributes = True


# ---- PortalAnnotation ----

class PortalAnnotationBase(BaseModel):
    day: date
    title: str = Field(..., max_length=255)
    kind: Literal["blog_post", "application", "deploy", "other"]
    ref: Optional[str] = Field(None, max_length=255)


class PortalAnnotationCreate(PortalAnnotationBase):
    site_id: str  # Obligatorio al crear


class PortalAnnotationUpdate(BaseModel):
    day: Optional[date] = None
    title: Optional[str] = Field(None, max_length=255)
    kind: Optional[Literal["blog_post", "application", "deploy", "other"]] = None
    ref: Optional[str] = Field(None, max_length=255)


class PortalAnnotationOut(PortalAnnotationBase):
    id: str
    user_id: str
    site_id: str
    created_at: datetime

    class Config:
        from_attributes = True
