"""
PortalVisitor Model - Anonymous pseudonymous visitor to a portal site.
Tracks first/last seen, visit count, first origin, bot detection, and owner flag.
"""
from sqlalchemy import Column, DateTime, ForeignKey, String, Boolean, Integer, UniqueConstraint
from sqlalchemy.sql import func
from database import Base
from services.id_generator import register_id_listener


class PortalVisitor(Base):
    """One pseudonymous visitor: first/last contact, visit count, detection flags."""

    __tablename__ = "portal_visitors"

    # --- Identificación ---
    id = Column(String(20), primary_key=True, index=True)
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    site_id = Column(String(20), ForeignKey("portal_sites.id", ondelete="CASCADE"), nullable=False, index=True)

    # --- Seguimiento ---
    visitor_key = Column(String(64), nullable=False, index=True)
    first_seen = Column(DateTime(timezone=True), nullable=False)
    last_seen = Column(DateTime(timezone=True), nullable=False)
    visit_count = Column(Integer, nullable=False, server_default="1", default=1)

    # --- Primer origen ---
    first_referrer_domain = Column(String(255), nullable=True)
    first_channel = Column(String(50), nullable=True)
    first_utm_source = Column(String(255), nullable=True)
    first_utm_medium = Column(String(255), nullable=True)
    first_utm_campaign = Column(String(255), nullable=True)

    # --- Ubicación ---
    country = Column(String(100), nullable=True, index=True)

    # --- Detección ---
    is_bot = Column(Boolean, nullable=False, server_default="false", default=False)
    bot_score = Column(Integer, nullable=False, server_default="0", default=0)
    is_owner = Column(Boolean, nullable=False, server_default="false", default=False)

    # --- Legado (evento anterior a la migración) ---
    legacy = Column(Boolean, nullable=False, server_default="false", default=False)

    # --- Auditoría temporal ---
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint("site_id", "visitor_key", name="uix_portal_visitors_site_visitor"),
    )

    def __repr__(self):
        return f"<PortalVisitor(id={self.id}, visitor_key='{self.visitor_key[:8]}...')>"


register_id_listener(PortalVisitor, "pvr")
