"""
Achievement Model - Concrete accomplishments (challenge/solution/impact).
Career domain (v2) - Identity.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, CheckConstraint, JSON
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


from services.id_generator import register_id_listener


class Achievement(Base):
    """A quantifiable achievement, optionally tied to a work history entry."""

    __tablename__ = "achievements"
    __table_args__ = (
        CheckConstraint("evidence_type IN ('direct_account', 'public_backed')"),
    )

    # --- Identificación (id prefijado + user_id para aislamiento) ---
    id = Column(String(20), primary_key=True, index=True)
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # --- Campos de negocio ---
    title = Column(String(255), nullable=False)
    work_history_id = Column(String(20), ForeignKey("work_history.id", ondelete="SET NULL"), nullable=True, index=True)
    context = Column(
        JSON().with_variant(postgresql.JSONB, "postgresql"), nullable=True)
    challenge = Column(Text, nullable=True)
    solution = Column(Text, nullable=True)
    impact_metrics = Column(
        JSON().with_variant(postgresql.JSONB, "postgresql"), nullable=True)
    evidence_type = Column(String(30), nullable=True)
    documentation_urls = Column(Text, nullable=True)
    executive_storytelling = Column(Text, nullable=True)
    demonstrated_competency_ids = Column(
        JSON().with_variant(postgresql.JSONB, "postgresql"), nullable=True)
    visible_on_cv = Column(Boolean, default=True, nullable=True)
    visible_in_interview = Column(Boolean, default=True, nullable=True)
    visible_on_portal = Column(Boolean, default=False, nullable=True)
    home = Column(Boolean, default=False, nullable=True, index=True)

    notes = Column(Text, nullable=True)

    work_history_record = relationship("WorkHistory", back_populates="linked_achievements")


    # --- Auditoría temporal ---
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<Achievement(id={self.id}, title='{self.title}')>"

register_id_listener(Achievement, "ach")
