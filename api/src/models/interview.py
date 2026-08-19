"""
Interview Model - Interviews held as part of a job application.
Career domain (v2) - Búsqueda.

NOTE: Replaces the legacy `models/interview.py` (deleted), whose columns
did not match the real `interviews` table (it had already caused a table
collision; the table was dropped and recreated with this schema).
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.sql import func
from database import Base


class Interview(Base):
    """An interview round for a job application."""

    __tablename__ = "interviews"
    __table_args__ = (
        CheckConstraint(
            "overall_impression IN ('very_positive', 'positive', 'neutral', 'negative')"
        ),
        CheckConstraint(
            "interview_result IN ('pending', 'advanced', 'rejected', 'under_consideration')"
        ),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    application_id = Column(
        Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    narrative_used_id = Column(
        Integer, ForeignKey("role_narratives.id", ondelete="SET NULL"), nullable=True
    )

    interview_type = Column(String(50), nullable=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    interviewers = Column(Text, nullable=True)
    questions_asked = Column(Text, nullable=True)
    answers_given = Column(Text, nullable=True)
    feedback_received = Column(Text, nullable=True)
    overall_impression = Column(String(20), nullable=True)
    interview_result = Column(String(30), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<Interview(id={self.id}, application_id={self.application_id})>"
