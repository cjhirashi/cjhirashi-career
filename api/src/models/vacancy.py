"""
Vacancy Model - Job opportunities tracking.
"""
from sqlalchemy import Column, Integer, ForeignKey, String, Text, DateTime, Boolean, Float, JSON, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
import enum


class VacancyStatus(str, enum.Enum):
    """Status of vacancy tracking."""
    INTERESTED = "interested"
    APPLIED = "applied"
    REJECTED = "rejected"
    ACCEPTED = "accepted"
    ARCHIVED = "archived"


class Vacancy(Base):
    """
    Job vacancy tracking for career planning.

    Supports:
    - Job opportunities of interest
    - Application tracking
    - Match scoring against skills/experience
    """

    __tablename__ = "vacancies"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Foreign Key
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Vacancy Details
    job_title = Column(String(255), nullable=False, index=True)
    company_name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    job_url = Column(String(500), nullable=True)

    # Position Details
    industry = Column(String(100), nullable=True)
    role_level = Column(String(100), nullable=True)
    employment_type = Column(String(100), nullable=True)  # full-time, part-time, contract, etc.

    # Compensation
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    currency = Column(String(10), nullable=True)
    benefits = Column(Text, nullable=True)

    # Location
    location = Column(String(255), nullable=True)
    remote_option = Column(String(100), nullable=True)

    # Timeline
    posting_date = Column(DateTime(timezone=True), nullable=True)
    deadline_date = Column(DateTime(timezone=True), nullable=True)

    # Application Tracking
    status = Column(Enum(VacancyStatus), default=VacancyStatus.INTERESTED, nullable=False, index=True)
    application_date = Column(DateTime(timezone=True), nullable=True)
    application_url = Column(String(500), nullable=True)

    # Matching & Scoring
    match_score = Column(Float, nullable=True)  # 0-100 based on skills match
    match_analysis = Column(JSON, nullable=True)  # Detailed matching analysis
    required_skills = Column(String(1000), nullable=True)
    matched_skills = Column(String(1000), nullable=True)
    missing_skills = Column(String(1000), nullable=True)

    # Contact & Notes
    contact_person = Column(String(255), nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(20), nullable=True)
    internal_contact = Column(String(255), nullable=True)  # Internal referral contact

    # Notes & Feedback
    notes = Column(Text, nullable=True)
    feedback = Column(Text, nullable=True)
    reason_for_rejection = Column(Text, nullable=True)

    # Metadata
    metadata = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="vacancies")

    def __repr__(self):
        return f"<Vacancy(id={self.id}, job_title='{self.job_title}', company='{self.company_name}')>"
