"""
Competency Model - Professional skills and competencies.
Career domain (v2) - Identity.
Classifies: technical, transferable, business.

NOTE: This file replaces a previous legacy version whose columns did not
match the real `competencies` table (collision risk fixed here).
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, Date, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from database import Base


class Competency(Base):
    """
    Professional competency or skill (technical, transferible or de negocio).
    """

    __tablename__ = "competencies"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False, index=True)  # technical | transferable | business
    category = Column(String(100), nullable=True)
    level = Column(String(50), nullable=True)
    years_of_experience = Column(Numeric(4, 2), nullable=True)
    practice_start_date = Column(Date, nullable=True)
    context_libraries = Column(JSONB, nullable=True)
    depth_description = Column(Text, nullable=True)
    market_gaps = Column(Text, nullable=True)
    honesty_note = Column(Text, nullable=True)
    aligned_differentiator_ids = Column(JSONB, nullable=True)
    proficiency_score = Column(Integer, nullable=True)
    is_highlighted = Column(Boolean, default=False, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<Competency(id={self.id}, name='{self.name}', type='{self.type}')>"
