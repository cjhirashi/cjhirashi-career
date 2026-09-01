"""
SearchPlan Model - Weekly/periodic job-search plans and targets.
Career domain (v2) - Búsqueda.
"""
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, CheckConstraint, JSON
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import func
from database import Base


from services.id_generator import register_id_listener


class SearchPlan(Base):
    """A job-search plan for a given period, with weekly targets and status."""

    __tablename__ = "search_plans"
    __table_args__ = (
        CheckConstraint(
            "plan_status IN ('not_started', 'in_progress', 'paused', 'completed', 'cancelled')"
        ),
    )

    # --- Identificación (id prefijado + user_id para aislamiento) ---
    id = Column(String(20), primary_key=True, index=True)
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    # --- Campos de negocio ---
    target_role_id = Column(String(20), ForeignKey("target_roles.id", ondelete="SET NULL"), nullable=True)

    period_start = Column(Date, nullable=True)
    period_end = Column(Date, nullable=True)
    weekly_targets = Column(
        JSON().with_variant(postgresql.JSONB, "postgresql"), nullable=True)
    primary_channels = Column(Text, nullable=True)
    target_cvs_sent = Column(Integer, nullable=True)
    target_interviews = Column(Integer, nullable=True)
    target_offers = Column(Integer, nullable=True)
    plan_status = Column(String(30), default="not_started", nullable=True)
    completion_percentage = Column(Integer, default=0, nullable=True)
    lessons_learned = Column(Text, nullable=True)

    notes = Column(Text, nullable=True)


    # --- Auditoría temporal ---
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<SearchPlan(id={self.id}, period_start={self.period_start})>"

register_id_listener(SearchPlan, "spl")
