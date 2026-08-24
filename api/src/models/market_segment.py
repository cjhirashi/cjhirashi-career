"""
MarketSegment Model - Visible/hidden market channels and their performance.
Career domain (v2) - Búsqueda.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.sql import func
from database import Base


from services.id_generator import register_id_listener


class MarketSegment(Base):
    """A job-search channel (visible or hidden market) with tracked results."""

    __tablename__ = "market_segments"
    __table_args__ = (
        CheckConstraint("market_type IN ('visible', 'hidden')"),
        CheckConstraint("priority BETWEEN 1 AND 10"),
    )

    id = Column(String(20), primary_key=True, index=True)
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    market_type = Column(String(20), nullable=True)
    channel_name = Column(String(255), nullable=True)
    channel_type = Column(String(50), nullable=True)
    strategy_text = Column(Text, nullable=True)
    applications_made = Column(Integer, default=0, nullable=True)
    responses_received = Column(Integer, default=0, nullable=True)
    interviews_achieved = Column(Integer, default=0, nullable=True)
    priority = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True, nullable=True)

    notes = Column(Text, nullable=True)


    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<MarketSegment(id={self.id}, channel_name='{self.channel_name}')>"

register_id_listener(MarketSegment, "mks")
