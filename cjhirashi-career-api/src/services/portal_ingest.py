"""
Portal analytics event ingestion service (v2).

Implements the exact ingestion pipeline per SPEC-0010 C2:
  1. Resolve site by siteKey or default
  2. Resolve or create visitor
  3. Acquire advisory lock (PostgreSQL only)
  4. Resolve or create visit
  5. Create event with seq
  6. Update visit counters and flags
  7. Evaluate key events

Never commits the transaction; the route does.
"""
import hashlib
import logging
import uuid
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models.application import Application
from models.portal_channel_rule import PortalChannelRule
from models.portal_event import PortalEvent
from models.portal_site import PortalSite
from models.portal_visitor import PortalVisitor
from models.portal_visit import PortalVisit
from models.portal_goal import PortalGoal
from schemas.events import TrackEventIn
from services.portal_bots import score_bot, is_bot
from services.portal_channels import classify_channel, extract_domain
from services.portal_device import parse_device
from services.portal_geo import resolve_request_geo

logger = logging.getLogger(__name__)

# Passive event types that allow attaching to old visits
PASSIVE_EVENTS = {"page_duration", "page_leave", "scroll", "web_vitals"}

# Threshold for visit inactivity (30 min)
VISIT_INACTIVITY_THRESHOLD_MS = 30 * 60 * 1000


def _header(headers: Mapping[str, str], name: str) -> str | None:
    for key, value in headers.items():
        if key.lower() == name:
            return value
    return None


class UnknownSite(Exception):
    """Raised when siteKey is unknown or no default site exists."""

    pass


def goal_matches(
    goal_type: str,
    match: dict,
    *,
    event_type: str,
    page: str,
    target_url: str | None,
) -> bool:
    """
    Evaluate if an event matches a goal definition.

    Goal types:
    - "event": event_type == match["event_type"]
    - "outbound": event_type == "outbound" and match["url_contains"] appears in target_url
    - "page": event_type == "pageview" and page starts with match["path_prefix"]
    - other: returns False

    Args:
        goal_type: Type of goal
        match: Match conditions dict
        event_type: Event type from the event
        page: Page path from the event
        target_url: Target URL from the event (if any)

    Returns:
        True if the event matches the goal, False otherwise
    """
    if goal_type == "event":
        return event_type == match.get("event_type")
    elif goal_type == "outbound":
        if event_type != "outbound":
            return False
        url_contains = match.get("url_contains", "").lower()
        return (
            target_url is not None
            and url_contains in target_url.lower()
        )
    elif goal_type == "page":
        if event_type != "pageview":
            return False
        path_prefix = match.get("path_prefix", "")
        return page.startswith(path_prefix)
    else:
        return False


async def ingest_event(
    db: AsyncSession,
    *,
    payload: TrackEventIn,
    headers: Mapping[str, str],
    ip: str | None,
    now: datetime | None = None,
) -> PortalEvent:
    """
    Ingest a single event into the portal analytics system.

    Implements the exact pipeline from SPEC-0010 C2, step by step.

    Args:
        db: AsyncSession (not auto-committed by this function)
        payload: The parsed TrackEventIn schema
        headers: Request headers (for geo, device parsing)
        ip: Client IP (for geo; never persisted per RF-005)
        now: Current timestamp (defaults to UTC now; server clock always used)

    Returns:
        The created PortalEvent

    Raises:
        UnknownSite: If siteKey is unknown or no default site exists
    """
    if now is None:
        now = datetime.now(timezone.utc)

    # =========================================================================
    # STEP 1: RESOLVE SITE
    # =========================================================================
    if payload.siteKey:
        # Search by public_key and active
        site_row = await db.execute(
            select(PortalSite).where(
                (PortalSite.public_key == payload.siteKey)
                & (PortalSite.active == True)  # noqa: E712
            )
        )
        site = site_row.scalar_one_or_none()
        if not site:
            raise UnknownSite(f"Unknown siteKey: {payload.siteKey}")
    else:
        # Use first active site with user_id == PUBLIC_PORTAL_USER_ID
        site_row = await db.execute(
            select(PortalSite).where(
                (PortalSite.user_id == settings.PUBLIC_PORTAL_USER_ID)
                & (PortalSite.active == True)  # noqa: E712
            ).order_by(PortalSite.created_at).limit(1)
        )
        site = site_row.scalar_one_or_none()
        if not site:
            raise UnknownSite("No active default portal site found")

    user_id = site.user_id

    # =========================================================================
    # STEP 2: RESOLVE VISITOR KEY
    # =========================================================================
    if payload.visitorId:
        visitor_key = payload.visitorId
        has_client_visitor_id = True
    else:
        visitor_key = f"anon-{payload.sessionId or uuid.uuid4().hex}"
        has_client_visitor_id = False

    # =========================================================================
    # STEP 3: ADVISORY LOCK (PostgreSQL only)
    # =========================================================================
    # If PostgreSQL, lock on (site.id, visitor_key) to serialize concurrent events
    dialect_name = db.bind.dialect.name if db.bind else None
    if dialect_name == "postgresql":
        lock_key = f"{site.id}:{visitor_key}"
        # hashtext is a PostgreSQL function that hashes a string to bigint
        await db.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:k))").bindparams(k=lock_key)
        )

    # =========================================================================
    # STEP 4: RESOLVE OR CREATE VISITOR
    # =========================================================================
    visitor_row = await db.execute(
        select(PortalVisitor).where(
            (PortalVisitor.site_id == site.id)
            & (PortalVisitor.visitor_key == visitor_key)
        )
    )
    visitor = visitor_row.scalar_one_or_none()

    if not visitor:
        visitor = PortalVisitor(
            user_id=user_id,
            site_id=site.id,
            visitor_key=visitor_key,
            first_seen=now,
            last_seen=now,
            visit_count=0,
            legacy=False,
        )
        db.add(visitor)
        await db.flush()

    # Check owner token
    if payload.ownerToken:
        token_hash = hashlib.sha256(payload.ownerToken.encode()).hexdigest()
        if token_hash == site.owner_token_hash:
            visitor.is_owner = True

    # =========================================================================
    # STEP 5: RESOLVE OR CREATE VISIT
    # =========================================================================
    # Passive event types
    is_passive = payload.type in PASSIVE_EVENTS

    # Find last visit by last_activity_at DESC
    last_visit_row = await db.execute(
        select(PortalVisit)
        .where(PortalVisit.visitor_id == visitor.id)
        .order_by(PortalVisit.last_activity_at.desc())
        .limit(1)
    )
    last_visit = last_visit_row.scalar_one_or_none()

    # (a) hueco < 30 min => visita vigente; (b) evento pasivo con hueco < 24 h => visita vigente
    #     (el aviso de salida llega tarde); en cualquier otro caso se abre una visita nueva.
    should_create_new_visit = True
    if last_visit:
        gap_s = (now - last_visit.last_activity_at).total_seconds()
        if gap_s < VISIT_INACTIVITY_THRESHOLD_MS / 1000:
            should_create_new_visit = False
        elif is_passive and gap_s < 24 * 60 * 60:
            should_create_new_visit = False

    # El User-Agent del payload manda; si falta se usa el de la cabecera.
    user_agent = payload.userAgent or _header(headers, "user-agent")

    # Parse geographic info
    geo_info = await resolve_request_geo(headers, ip)

    # Parse device info
    accept_language = _header(headers, "accept-language")

    device_info = parse_device(
        user_agent,
        accept_language=accept_language,
        screen=payload.screen,
    )

    if should_create_new_visit or not last_visit:
        # Create new visit
        referrer_domain = extract_domain(payload.referrer)

        rules_rows = await db.execute(
            select(PortalChannelRule)
            .where(PortalChannelRule.site_id == site.id)
            .order_by(PortalChannelRule.priority)
        )
        channel_rules = [
            {"priority": r.priority, "channel": r.channel, "conditions": r.conditions or {}}
            for r in rules_rows.scalars().all()
        ]

        # Postulación: utm_campaign igual al id de una postulación del dueño.
        campaign = (payload.utm or {}).get("utm_campaign")
        application_id = None
        if campaign:
            application_id = (
                await db.execute(
                    select(Application.id).where(
                        (Application.user_id == user_id) & (Application.id == campaign.strip().lower())
                    )
                )
            ).scalar_one_or_none()

        # Classify channel based on rules
        channel = classify_channel(
            channel_rules,
            referrer_domain=referrer_domain,
            utm_source=payload.utm.get("utm_source") if payload.utm else None,
            utm_medium=payload.utm.get("utm_medium") if payload.utm else None,
            own_domains=site.allowed_hosts or [],
        )

        # Get source
        source = (
            payload.utm.get("utm_source") if payload.utm else None
        ) or referrer_domain

        # Score bot
        bot_score, bot_reasons = score_bot(
            user_agent=user_agent,
            accept_language=accept_language,
            has_client_visitor_id=has_client_visitor_id,
            finished=False,
            pageviews=0,
            active_ms=0,
            max_scroll_pct=0,
        )

        visit = PortalVisit(
            user_id=user_id,
            site_id=site.id,
            visitor_id=visitor.id,
            started_at=now,
            last_activity_at=now,
            entry_page=payload.page,
            exit_page=payload.page if payload.type == "pageview" else None,
            referrer_url=payload.referrer,
            referrer_domain=referrer_domain,
            utm_source=payload.utm.get("utm_source") if payload.utm else None,
            utm_medium=payload.utm.get("utm_medium") if payload.utm else None,
            utm_campaign=payload.utm.get("utm_campaign") if payload.utm else None,
            utm_content=payload.utm.get("utm_content") if payload.utm else None,
            utm_term=payload.utm.get("utm_term") if payload.utm else None,
            click_id_type=(
                next(iter(payload.clickIds.keys())) if payload.clickIds else None
            ),
            channel=channel,
            source=source,
            device_type=device_info.get("device_type"),
            browser=device_info.get("browser"),
            browser_version=device_info.get("browser_version"),
            os=device_info.get("os"),
            os_version=device_info.get("os_version"),
            screen_size=device_info.get("screen_size"),
            language=device_info.get("language"),
            country=geo_info.country if geo_info else None,
            region=geo_info.region if geo_info else None,
            city=geo_info.city if geo_info else None,
            latitude=geo_info.latitude if geo_info else None,
            longitude=geo_info.longitude if geo_info else None,
            timezone=geo_info.timezone if geo_info else None,
            is_bot=is_bot(bot_score),
            bot_score=bot_score,
            bot_reasons=bot_reasons,
            is_owner=visitor.is_owner,
            is_new_visitor=(visitor.visit_count == 0),
            pageviews=0,
            events_count=0,
            active_ms=0,
            max_scroll_pct=0,
            is_engaged=False,
            is_bounce=True,
            converted=False,
            application_id=application_id,
        )
        db.add(visit)
        await db.flush()

        # If new visitor, copy first_* fields to visitor
        if visitor.visit_count == 0:
            visitor.first_referrer_domain = referrer_domain
            visitor.first_channel = channel
            visitor.first_utm_source = (
                payload.utm.get("utm_source") if payload.utm else None
            )
            visitor.first_utm_medium = (
                payload.utm.get("utm_medium") if payload.utm else None
            )
            visitor.first_utm_campaign = (
                payload.utm.get("utm_campaign") if payload.utm else None
            )
            if geo_info:
                visitor.country = geo_info.country
        visitor.visit_count += 1

    else:
        # Reuse last visit
        visit = last_visit

    # =========================================================================
    # STEP 6: CREATE EVENT
    # =========================================================================
    if visitor.is_owner:
        visit.is_owner = True

    seq = visit.events_count + 1

    # Prepare event_metadata (props with vitals embedded if present)
    event_props = payload.props or {}
    if payload.vitals:
        event_props = {**event_props, "vitals": payload.vitals}

    # Truncate to 500
    if user_agent and len(user_agent) > 500:
        user_agent = user_agent[:500]

    event = PortalEvent(
        user_id=user_id,
        site_id=site.id,
        visitor_id=visitor.id,
        visit_id=visit.id,
        seq=seq,
        event_type=payload.type,
        page=payload.page,
        page_title=payload.title,
        target=payload.target,
        target_url=payload.targetUrl,
        scroll_pct=payload.scrollPct,
        active_ms=payload.activeMs,
        session_id=payload.sessionId,
        country=visit.country,
        region=visit.region,
        city=visit.city,
        latitude=visit.latitude,
        longitude=visit.longitude,
        user_agent=user_agent,
        props=event_props if event_props else None,
        event_metadata=payload.metadata,
    )
    db.add(event)
    await db.flush()

    # =========================================================================
    # STEP 7: UPDATE VISIT COUNTERS
    # =========================================================================
    visit.events_count = seq
    visit.last_activity_at = max(visit.last_activity_at, now)
    visit.updated_at = now

    # Pageviews counter
    if payload.type == "pageview":
        visit.pageviews += 1
        visit.exit_page = payload.page

    # Active time (only for page_duration and page_leave)
    if payload.type in {"page_duration", "page_leave"}:
        active_val = (
            payload.activeMs
            if payload.activeMs is not None
            else payload.durationMs
        )
        if active_val is not None:
            # Cap per page at 30 min
            visit.active_ms += min(active_val, 30 * 60 * 1000)

    # Max scroll
    if payload.scrollPct is not None:
        visit.max_scroll_pct = max(visit.max_scroll_pct, payload.scrollPct)

    # =========================================================================
    # STEP 8: EVALUATE KEY EVENTS AND UPDATE ENGAGEMENT
    # =========================================================================
    # Load goals with is_key_event=True for this site
    goals_row = await db.execute(
        select(PortalGoal).where(
            (PortalGoal.site_id == site.id)
            & (PortalGoal.is_key_event == True)  # noqa: E712
        )
    )
    key_goals = goals_row.scalars().all()

    converted = False
    for goal in key_goals:
        if goal_matches(
            goal.type,
            goal.match,
            event_type=payload.type,
            page=payload.page,
            target_url=payload.targetUrl,
        ):
            converted = True
            break

    if converted:
        visit.converted = True

    # Update engagement flags
    is_engaged = (
        visit.active_ms > 10000
        or visit.pageviews >= 2
        or visit.converted
    )
    visit.is_engaged = is_engaged
    visit.is_bounce = not is_engaged

    # Update visitor
    visitor.last_seen = now
    if visit.is_bot:
        visitor.is_bot = True  # Only gets set to True, never back to False

    return event
