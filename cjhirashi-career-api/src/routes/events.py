"""
Public, unauthenticated ingestion for portfolio traffic events, sent by the
portfolio frontend's `trackingApi`. Every event belongs to a measured site
(`portal_sites`); payloads without `siteKey` (v1) go to the portal owner's
default site. See services/portal_ingest.py for the visit/visitor pipeline.

Never surfaces internal failures to the visitor: a flaky DB write or geo
lookup returns 204 (the frontend treats tracking as fire-and-forget). Only
client misconfiguration is rejected: unknown site (403), disallowed origin
(403) and abusive rate (429).
"""
import logging
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.portal_site import PortalSite
from models.portal_visitor import PortalVisitor
from schemas.events import TrackEventIn
from services.portal_ingest import ForbiddenOrigin, UnknownSite, ingest_event
from services.portal_ratelimit import SlidingWindowLimiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/events", tags=["Portal Events"])

# 120 eventos por minuto por visitante: un lector normal genera menos de 20.
_visitor_limiter = SlidingWindowLimiter(limit=120)
# 600 por minuto por IP cubre una oficina detrás de un NAT sin dejar abierta la puerta.
_ip_limiter = SlidingWindowLimiter(limit=600)


def _client_ip(request: Request) -> str | None:
    """Real visitor IP. This site sits behind Cloudflare Tunnel -> Caddy:
    Caddy's own hop resets X-Forwarded-For to the tunnel's internal IP, but
    Cloudflare always sets CF-Connecting-IP to the true original visitor
    (verified empirically against the live chain, not assumed) - that one
    takes priority. X-Forwarded-For and request.client.host are only
    fallbacks for requests that somehow bypass Cloudflare. The IP is used for
    rate limiting and the geo fallback only; it is never persisted."""
    cf_ip = request.headers.get("cf-connecting-ip")
    if cf_ip:
        return cf_ip.strip()
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


def _origin_host(request: Request) -> str | None:
    origin = request.headers.get("origin") or request.headers.get("referer")
    if not origin:
        return None
    return urlparse(origin).hostname


@router.post("/track", status_code=status.HTTP_204_NO_CONTENT)
async def track_event(event: TrackEventIn, request: Request, db: AsyncSession = Depends(get_db)):
    ip = _client_ip(request)
    visitor_key = event.visitorId or event.sessionId or ip or "unknown"
    if not _visitor_limiter.allow(visitor_key) or not _ip_limiter.allow(ip or "unknown"):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")

    try:
        await ingest_event(
            db, payload=event, headers=request.headers, ip=ip, origin_host=_origin_host(request)
        )
        await db.commit()
    except (UnknownSite, ForbiddenOrigin) as exc:
        await db.rollback()
        logger.warning("track_event rejected: %s", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Event rejected") from exc
    except Exception:
        await db.rollback()
        logger.exception("track_event: failed to persist event (page=%s, type=%s)", event.page, event.type)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


class ForgetIn(BaseModel):
    siteKey: str = Field(..., max_length=32)
    visitorId: str = Field(..., max_length=64, pattern=r"^[A-Za-z0-9_-]+$")


@router.post("/forget", status_code=status.HTTP_204_NO_CONTENT)
async def forget_visitor(body: ForgetIn, request: Request, db: AsyncSession = Depends(get_db)):
    """Self-service erasure: a visitor deletes their own visitor, visits and events.

    Always answers 204 whether or not the visitor existed, so the endpoint cannot
    be used to probe which visitor ids exist.
    """
    if not _ip_limiter.allow(_client_ip(request) or "unknown"):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")
    try:
        site = (
            await db.execute(select(PortalSite).where(PortalSite.public_key == body.siteKey, PortalSite.active.is_(True)))
        ).scalar_one_or_none()
        if site is not None:
            await db.execute(
                delete(PortalVisitor).where(PortalVisitor.site_id == site.id, PortalVisitor.visitor_key == body.visitorId)
            )
            await db.commit()
    except Exception:
        await db.rollback()
        logger.exception("forget_visitor failed")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
