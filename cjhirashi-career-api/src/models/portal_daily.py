"""
PortalDaily Model - Lazy-computed daily rollup of portal analytics by dimension.
Aggregates clean (non-bot, non-owner) traffic and supports recalculation.
"""
from sqlalchemy import Column, DateTime, ForeignKey, String, Integer, Date, UniqueConstraint
from sqlalchemy.sql import func
from database import Base
from services.id_generator import register_id_listener


class PortalDaily(Base):
    """One daily rollup for a site, dimension, and key: counts and engagement metrics."""

    __tablename__ = "portal_daily"

    # --- Identificación ---
    id = Column(String(20), primary_key=True, index=True)
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    site_id = Column(String(20), ForeignKey("portal_sites.id", ondelete="CASCADE"), nullable=False, index=True)

    # --- Dimensión temporal y de análisis ---
    day = Column(Date, nullable=False)
    dimension = Column(String(50), nullable=False)  # total|page|entry_page|exit_page|channel|source|country|device|browser|os|campaign
    key = Column(String(255), nullable=False)  # value for the dimension (or empty for 'total')

    # --- Métricas ---
    visitors = Column(Integer, nullable=False, server_default="0", default=0)
    visits = Column(Integer, nullable=False, server_default="0", default=0)
    pageviews = Column(Integer, nullable=False, server_default="0", default=0)
    engaged_visits = Column(Integer, nullable=False, server_default="0", default=0)
    bounces = Column(Integer, nullable=False, server_default="0", default=0)
    active_ms_sum = Column(Integer, nullable=False, server_default="0", default=0)
    conversions = Column(Integer, nullable=False, server_default="0", default=0)

    # --- Metadata de cálculo ---
    computed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("site_id", "day", "dimension", "key", name="uix_portal_daily_dimension"),
    )

    def __repr__(self):
        return f"<PortalDaily(id={self.id}, day={self.day}, dimension='{self.dimension}', key='{self.key}')>"


register_id_listener(PortalDaily, "pdy")
