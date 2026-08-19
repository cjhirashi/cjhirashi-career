"""
WorkHistory Model - Past positions / employment history.
Career domain (v2) - Identity.
"""
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from database import Base


class WorkHistory(Base):
    """A position held by the user at a company."""

    __tablename__ = "work_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    company = Column(String(255), nullable=False)
    role_title = Column(String(255), nullable=False)
    start_date = Column(Date, nullable=True, index=True)
    end_date = Column(Date, nullable=True)
    people_managed = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    narrative = Column(Text, nullable=True)
    achievements = Column(JSONB, nullable=True)
    key_metrics = Column(JSONB, nullable=True)
    learnings = Column(Text, nullable=True)
    contract_type = Column(String(50), nullable=True)
    industry_sector = Column(String(100), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<WorkHistory(id={self.id}, company='{self.company}', role_title='{self.role_title}')>"
