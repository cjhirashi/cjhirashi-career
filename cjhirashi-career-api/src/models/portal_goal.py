"""
PortalGoal Model - Definition of a conversion goal/metric.
Goals can be event-based, page-based, outbound, or engagement-based.
"""
from sqlalchemy import Column, DateTime, ForeignKey, String, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from database import Base
from services.id_generator import register_id_listener


class PortalGoal(Base):
    """One conversion goal: event/page/outbound/engagement match."""

    __tablename__ = "portal_goals"

    # --- Identificación ---
    id = Column(String(20), primary_key=True, index=True)
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    site_id = Column(String(20), ForeignKey("portal_sites.id", ondelete="CASCADE"), nullable=False, index=True)

    # --- Definición ---
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)  # event|page|outbound|min_active|min_pages
    match = Column(JSONB, nullable=False)  # conditions/payload
    is_key_event = Column(Boolean, nullable=False, server_default="false", default=False)

    # --- Auditoría temporal ---
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    def __repr__(self):
        return f"<PortalGoal(id={self.id}, name='{self.name}', type='{self.type}')>"


register_id_listener(PortalGoal, "pgl")
