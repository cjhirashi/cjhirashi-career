"""
CareerReview Model - Periodic gap analysis / transition decisions / quarterly reviews.
Career domain (v2) - Identity.
"""
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.sql import func
from database import Base


from services.id_generator import register_id_listener


class CareerReview(Base):
    """A career review entry: gap analysis, transition decision or quarterly review."""

    __tablename__ = "career_reviews"
    __table_args__ = (
        CheckConstraint("review_type IN ('gap_analysis', 'transition_decision', 'quarterly_review')"),
        CheckConstraint("tracking_status IN ('active', 'completed', 'paused')"),
    )

    id = Column(String(20), primary_key=True, index=True)
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    review_date = Column(Date, nullable=True)
    review_type = Column(String(50), nullable=True)
    context = Column(Text, nullable=True)
    decision_or_finding = Column(Text, nullable=True)
    result_or_learning = Column(Text, nullable=True)
    action_items = Column(Text, nullable=True)
    tracking_status = Column(String(30), default="active", nullable=True)

    notes = Column(Text, nullable=True)


    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<CareerReview(id={self.id}, review_type='{self.review_type}')>"

register_id_listener(CareerReview, "crv")
