"""
Public, unauthenticated ingestion for portfolio traffic events
(pageview/click/download), sent by the portfolio frontend's `trackingApi`.
Mirrors the read-only /public/* router's scoping: every event belongs to the
single portal owner (settings.PUBLIC_PORTAL_USER_ID).

Never raises to the caller: a flaky DB write or geo lookup must not surface
as an error in the visitor's browser (the frontend already treats tracking
failures as fire-and-forget), so everything here is best-effort.
"""
import logging

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from config import settings
from models.portal_event import PortalEvent
from schemas.events import TrackEventIn
from services.geo_ip_service import resolve_geo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/events", tags=["Portal Events"])

USER_ID = settings.PUBLIC_PORTAL_USER_ID


def _client_ip(request: Request) -> str | None:
    """Real visitor IP. This site sits behind Cloudflare Tunnel -> Caddy:
    Caddy's own hop resets X-Forwarded-For to the tunnel's internal IP, but
    Cloudflare always sets CF-Connecting-IP to the true original visitor
    (verified empirically against the live chain, not assumed) - that one
    takes priority. X-Forwarded-For and request.client.host are only
    fallbacks for requests that somehow bypass Cloudflare."""
    cf_ip = request.headers.get("cf-connecting-ip")
    if cf_ip:
        return cf_ip.strip()
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


@router.post("/track", status_code=status.HTTP_204_NO_CONTENT)
async def track_event(event: TrackEventIn, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        geo = await resolve_geo(_client_ip(request))
        record = PortalEvent(
            user_id=USER_ID,
            event_type=event.type,
            page=event.page,
            target=event.target,
            event_metadata=event.metadata,
            session_id=event.sessionId,
            duration_ms=event.durationMs,
            country=geo.country if geo else None,
            region=geo.region if geo else None,
            city=geo.city if geo else None,
            latitude=geo.latitude if geo else None,
            longitude=geo.longitude if geo else None,
            user_agent=event.userAgent,
        )
        db.add(record)
        await db.commit()
    except Exception:
        logger.exception("track_event: failed to persist event (page=%s, type=%s)", event.page, event.type)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
