"""
Interview Model - Job interview tracking and preparation.
"""
from sqlalchemy import Column, Integer, ForeignKey, String, Text, DateTime, Enum, Float, Boolean, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
import enum


class InterviewType(str, enum.Enum):
    """Type of interview."""
    PHONE_SCREENING = "phone_screening"
    VIDEO_CALL = "video_call"
    IN_PERSON = "in_person"
    TECHNICAL_TEST = "technical_test"
    CASE_STUDY = "case_study"
    PANEL_INTERVIEW = "panel_interview"
    FINAL = "final"
    OTHER = "other"


class InterviewRound(str, enum.Enum):
    """Interview round number."""
    FIRST_ROUND = "first_round"
    SECOND_ROUND = "second_round"
    THIRD_ROUND = "third_round"
    FINAL_ROUND = "final_round"


class InterviewFeedback(str, enum.Enum):
    """Interview feedback/outcome."""
    PENDING = "pending"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    ADVANCE = "advance"
    REJECTED = "rejected"
    ACCEPTED = "accepted"


class Interview(Base):
    """
    Job interview record and preparation tracking.

    Supports:
    - Interview scheduling and details
    - Preparation notes and resources
    - Performance feedback and scoring
    - Salary negotiation tracking
    """

    __tablename__ = "interviews"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Foreign Key
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Interview Details
    job_title = Column(String(255), nullable=False, index=True)
    company_name = Column(String(255), nullable=False, index=True)
    interview_type = Column(Enum(InterviewType), nullable=False, index=True)
    interview_round = Column(Enum(InterviewRound), nullable=True)

    # Scheduled Date & Time
    scheduled_date = Column(DateTime(timezone=True), nullable=True, index=True)
    duration_minutes = Column(Integer, nullable=True)
    timezone = Column(String(50), nullable=True)

    # Interviewer Information
    interviewer_name = Column(String(255), nullable=True)
    interviewer_title = Column(String(255), nullable=True)
    interviewer_email = Column(String(255), nullable=True)
    interviewer_phone = Column(String(20), nullable=True)

    # Meeting Details
    meeting_link = Column(String(500), nullable=True)
    meeting_location = Column(String(500), nullable=True)
    meeting_platform = Column(String(100), nullable=True)  # Zoom, Teams, Google Meet, etc.

    # Preparation
    preparation_notes = Column(Text, nullable=True)
    questions_to_ask = Column(Text, nullable=True)
    company_research = Column(Text, nullable=True)
    role_analysis = Column(Text, nullable=True)
    practice_answers = Column(JSON, nullable=True)  # Key talking points

    # Resources
    interview_resources = Column(String(1000), nullable=True)  # Links to preparation materials
    relevant_evidence_ids = Column(String(500), nullable=True)  # References to Evidence items

    # Performance Feedback
    feedback = Column(Enum(InterviewFeedback), default=InterviewFeedback.PENDING, nullable=False, index=True)
    performance_score = Column(Float, nullable=True)  # 0-100
    interviewer_feedback = Column(Text, nullable=True)
    your_impressions = Column(Text, nullable=True)

    # Strengths & Weaknesses Observed
    strengths_demonstrated = Column(String(500), nullable=True)
    areas_for_improvement = Column(String(500), nullable=True)
    hiring_signals = Column(Text, nullable=True)

    # Salary & Compensation
    salary_discussed = Column(Boolean, default=False, nullable=False)
    salary_offered = Column(Float, nullable=True)
    benefits_discussed = Column(Text, nullable=True)
    negotiation_notes = Column(Text, nullable=True)

    # Follow-up
    follow_up_date = Column(DateTime(timezone=True), nullable=True)
    follow_up_status = Column(String(255), nullable=True)
    next_steps = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)

    # Timeline
    completed_date = Column(DateTime(timezone=True), nullable=True)

    # Notes & Metadata
    notes = Column(Text, nullable=True)
    extra_metadata = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="interviews")

    def __repr__(self):
        return f"<Interview(id={self.id}, job_title='{self.job_title}', company='{self.company_name}')>"
