"""
FitScoringFactor Model - Weighted factors used to score vacancy fit.
Career domain (v2) - Búsqueda.
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey
from database import Base


class FitScoringFactor(Base):
    """A weighted factor used to compute how well a vacancy fits the user."""

    __tablename__ = "fit_scoring_factors"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    factor_name = Column(String(100), nullable=False)
    weight_percentage = Column(Integer, nullable=True)
    scoring_guide = Column(Text, nullable=True)
    display_order = Column(Integer, nullable=True)

    def __repr__(self):
        return f"<FitScoringFactor(id={self.id}, factor_name='{self.factor_name}')>"
