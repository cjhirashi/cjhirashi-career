"""
PortalChannelRule Model - Editable rules for deriving traffic channel from referrer/UTM.
Rules are ordered by priority and use JSONB conditions similar to GA4.
"""
from sqlalchemy import Column, DateTime, ForeignKey, String, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from database import Base
from services.id_generator import register_id_listener


class PortalChannelRule(Base):
    """One channel derivation rule: priority, channel name, and JSONB conditions."""

    __tablename__ = "portal_channel_rules"

    # --- Identificación ---
    id = Column(String(20), primary_key=True, index=True)
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    site_id = Column(String(20), ForeignKey("portal_sites.id", ondelete="CASCADE"), nullable=False, index=True)

    # --- Regla ---
    priority = Column(Integer, nullable=False, default=0)
    channel = Column(String(50), nullable=False)
    conditions = Column(JSONB, nullable=False)  # {utm_medium_in: [...], referrer_domain_in: [...], ...}

    # --- Auditoría temporal ---
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    def __repr__(self):
        return f"<PortalChannelRule(id={self.id}, priority={self.priority}, channel='{self.channel}')>"


register_id_listener(PortalChannelRule, "pcr")
