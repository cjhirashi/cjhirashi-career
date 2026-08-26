"""
RoleGapAnalysis Model - Skill/experience gaps against a target role.
Career domain (v2) - Identity.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.sql import func
from database import Base


from services.id_generator import register_id_listener


class RoleGapAnalysis(Base):
    """A specific gap identified for a target role, with closing plan and status."""

    __tablename__ = "role_gap_analysis"
    __table_args__ = (
        CheckConstraint("severity IN ('critical', 'high', 'medium', 'low')"),
        CheckConstraint("viability IN ('viable', 'viable_with_caveats', 'not_viable')"),
        CheckConstraint("closure_status IN ('not_started', 'in_progress', 'completed', 'paused')"),
    )

    # --- Identificación (id prefijado + user_id para aislamiento) ---
    id = Column(String(20), primary_key=True, index=True)
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    # --- Campos de negocio ---
    target_role_id = Column(String(20), ForeignKey("target_roles.id", ondelete="CASCADE"), nullable=False, index=True)

    gap_name = Column(String(255), nullable=False)
    severity = Column(String(20), nullable=True)
    market_requirement = Column(Text, nullable=True)
    closing_plan = Column(Text, nullable=True)
    viability = Column(String(30), nullable=True)
    closure_status = Column(String(30), default="not_started", nullable=True)

    notes = Column(Text, nullable=True)


    # --- Auditoría temporal ---
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<RoleGapAnalysis(id={self.id}, gap_name='{self.gap_name}')>"

register_id_listener(RoleGapAnalysis, "rga")
