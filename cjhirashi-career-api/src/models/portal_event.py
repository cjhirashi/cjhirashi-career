"""
PortalEvent Model - Anonymous traffic events from the public portfolio site
(pageview/click/download), captured by POST /events/track. Scoped to the
single portal owner like every other table, even though the visitors
themselves are anonymous. Country/region/city are resolved server-side from
the request IP at ingestion time (see routes/events.py); the raw IP itself
is never persisted.
Career domain (v2) - Presencia Digital.
"""
from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from database import Base


from services.id_generator import register_id_listener


class PortalEvent(Base):
    """One pageview/click/download event from an anonymous portfolio visitor."""

    __tablename__ = "portal_events"

    # --- Identificación (id prefijado + user_id para aislamiento) ---
    id = Column(String(20), primary_key=True, index=True)
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # --- Campos heredados de negocio (v1) ---
    event_type = Column(String(30), nullable=False, index=True)
    page = Column(String(500), nullable=False, index=True)
    target = Column(String(255), nullable=True)
    # Identifica la pestaña/sesión de navegador del visitante (sessionStorage
    # del lado del portfolio, no un visitante persistente) - agrupa varios
    # pageviews en una sola "visita" en vez de contar cada uno por separado.
    session_id = Column(String(64), nullable=True, index=True)
    # Only set on `event_type == "page_duration"` events (one per page visit,
    # sent via sendBeacon on route change / tab close) - how long the visitor
    # actually stayed, in milliseconds.
    duration_ms = Column(Integer, nullable=True)
    event_metadata = Column(JSONB, nullable=True)
    country = Column(String(100), nullable=True, index=True)
    region = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    # Ciudad aproximada (cabeceras de Cloudflare) - alimenta el mapa de burbujas de Métricas.
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    user_agent = Column(String(500), nullable=True)

    # --- Campos nuevos (v2) para analítica multi-sitio ---
    site_id = Column(String(20), ForeignKey("portal_sites.id", ondelete="CASCADE"), nullable=True, index=True)
    visitor_id = Column(String(20), ForeignKey("portal_visitors.id", ondelete="CASCADE"), nullable=True, index=True)
    visit_id = Column(String(20), ForeignKey("portal_visits.id", ondelete="CASCADE"), nullable=True, index=True)
    seq = Column(Integer, nullable=True)  # Orden dentro de la visita
    page_title = Column(String(500), nullable=True)
    props = Column(JSONB, nullable=True)  # Reutiliza event_metadata para compatibilidad
    scroll_pct = Column(Integer, nullable=True)
    active_ms = Column(Integer, nullable=True)
    target_url = Column(String(1024), nullable=True)

    # --- Auditoría temporal ---
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    __table_args__ = (
        Index("ix_portal_events_site_created_at", "site_id", "created_at"),
        Index("ix_portal_events_visit_seq", "visit_id", "seq"),
        Index("ix_portal_events_visitor_created_at", "visitor_id", "created_at"),
    )

    def __repr__(self):
        return f"<PortalEvent(id={self.id}, event_type='{self.event_type}', page='{self.page}')>"

register_id_listener(PortalEvent, "pev")
