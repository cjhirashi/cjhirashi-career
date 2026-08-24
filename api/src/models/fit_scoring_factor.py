"""
FitScoringFactor Model - Weighted factors used to score vacancy fit.
Career domain (v2) - Búsqueda.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base


from services.id_generator import register_id_listener


class FitScoringFactor(Base):
    """A weighted factor used to compute how well a vacancy fits the user."""

    __tablename__ = "fit_scoring_factors"

    id = Column(String(20), primary_key=True, index=True)
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    factor_name = Column(String(100), nullable=False)
    weight_percentage = Column(Integer, nullable=True)
    scoring_guide = Column(Text, nullable=True)
    display_order = Column(Integer, nullable=True)

    notes = Column(Text, nullable=True)


    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<FitScoringFactor(id={self.id}, factor_name='{self.factor_name}')>"

register_id_listener(FitScoringFactor, "fsf")
