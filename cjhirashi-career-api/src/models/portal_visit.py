"""
PortalVisit Model - One visit session of an anonymous visitor.
Tracks entry/exit pages, referrer, UTM, device, geography, engagement and conversion.
"""
from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Boolean, Integer, Float
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from database import Base
from services.id_generator import register_id_listener


class PortalVisit(Base):
    """One visit session: entry/exit, referrer, UTM, device, geography, engagement."""

    __tablename__ = "portal_visits"

    # --- Identificación ---
    id = Column(String(20), primary_key=True, index=True)
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    site_id = Column(String(20), ForeignKey("portal_sites.id", ondelete="CASCADE"), nullable=False, index=True)
    visitor_id = Column(String(20), ForeignKey("portal_visitors.id", ondelete="CASCADE"), nullable=False, index=True)

    # --- Temporización ---
    started_at = Column(DateTime(timezone=True), nullable=False)
    last_activity_at = Column(DateTime(timezone=True), nullable=False)

    # --- Páginas y referrer ---
    entry_page = Column(String(500), nullable=False)
    exit_page = Column(String(500), nullable=True)
    referrer_url = Column(String(1024), nullable=True)
    referrer_domain = Column(String(255), nullable=True)

    # --- UTM y click ids ---
    utm_source = Column(String(255), nullable=True)
    utm_medium = Column(String(255), nullable=True)
    utm_campaign = Column(String(255), nullable=True)
    utm_content = Column(String(255), nullable=True)
    utm_term = Column(String(255), nullable=True)
    click_id_type = Column(String(50), nullable=True)  # gclid, fbclid, etc.

    # --- Canal derivado ---
    channel = Column(String(50), nullable=True)
    source = Column(String(255), nullable=True)

    # --- Dispositivo ---
    device_type = Column(String(50), nullable=True)  # mobile, tablet, desktop
    browser = Column(String(100), nullable=True)
    browser_version = Column(String(50), nullable=True)
    os = Column(String(100), nullable=True)
    os_version = Column(String(50), nullable=True)
    screen_size = Column(String(50), nullable=True)
    language = Column(String(20), nullable=True)

    # --- Geografía ---
    country = Column(String(100), nullable=True)
    region = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    timezone = Column(String(50), nullable=True)

    # --- Detección ---
    is_bot = Column(Boolean, nullable=False, server_default="false", default=False)
    bot_score = Column(Integer, nullable=False, server_default="0", default=0)
    bot_reasons = Column(JSONB, nullable=True, server_default="[]")
    is_owner = Column(Boolean, nullable=False, server_default="false", default=False)
    is_new_visitor = Column(Boolean, nullable=False, server_default="false", default=False)

    # --- Métricas ---
    pageviews = Column(Integer, nullable=False, server_default="1", default=1)
    events_count = Column(Integer, nullable=False, server_default="1", default=1)
    active_ms = Column(Integer, nullable=False, server_default="0", default=0)
    max_scroll_pct = Column(Integer, nullable=False, server_default="0", default=0)

    # --- Engagement y conversión ---
    is_engaged = Column(Boolean, nullable=False, server_default="false", default=False)
    is_bounce = Column(Boolean, nullable=False, server_default="true", default=True)
    converted = Column(Boolean, nullable=False, server_default="false", default=False)

    # --- Vinculación a postulación ---
    application_id = Column(String(20), nullable=True)

    # --- Auditoría temporal ---
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, index=True)

    __table_args__ = (
        Index("ix_portal_visits_site_started", "site_id", "started_at"),
        Index("ix_portal_visits_visitor_activity", "visitor_id", last_activity_at.desc()),
        Index("ix_portal_visits_site_channel_started", "site_id", "channel", "started_at"),
        Index("ix_portal_visits_site_country_started", "site_id", "country", "started_at"),
        Index("ix_portal_visits_application", "application_id"),
    )

    def __repr__(self):
        return f"<PortalVisit(id={self.id}, visitor_id={self.visitor_id})>"


register_id_listener(PortalVisit, "pvs")
