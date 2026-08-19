"""
Differentiator Model - Professional differentiation pillars.
Career domain (v2) - Identity.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base


class Differentiator(Base):
    """What makes the user stand out: pillars of differentiation with supporting evidence."""

    __tablename__ = "differentiators"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    pillar_name = Column(String(255), nullable=False)
    pillar_description = Column(Text, nullable=True)
    strengths = Column(Text, nullable=True)
    evidence = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<Differentiator(id={self.id}, pillar_name='{self.pillar_name}')>"
