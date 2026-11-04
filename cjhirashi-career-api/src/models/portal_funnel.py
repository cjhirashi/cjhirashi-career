"""
PortalFunnel Model - Definition of a multi-step conversion funnel.
Each funnel has steps with labels, types, and match conditions.
"""
from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from database import Base
from services.id_generator import register_id_listener


class PortalFunnel(Base):
    """One multi-step funnel: steps with labels, types, and match conditions."""

    __tablename__ = "portal_funnels"

    # --- Identificación ---
    id = Column(String(20), primary_key=True, index=True)
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    site_id = Column(String(20), ForeignKey("portal_sites.id", ondelete="CASCADE"), nullable=False, index=True)

    # --- Definición ---
    name = Column(String(255), nullable=False)
    steps = Column(JSONB, nullable=False)  # [{label, type, match}, ...]

    # --- Auditoría temporal ---
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    def __repr__(self):
        return f"<PortalFunnel(id={self.id}, name='{self.name}')>"


register_id_listener(PortalFunnel, "pfn")
