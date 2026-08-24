"""
Metrics Model - User profile metrics and statistics.
Read-only model computed from events and evidence.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, JSON, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class Metrics(Base):
    """
    Pre-computed metrics and statistics for user profiles.

    Read-only aggregated data for:
    - Profile completeness
    - Activity statistics
    - Career progression metrics
    - Skill assessment

    This table is computed periodically from Events and Evidence tables.
    Not meant to be manually edited via API.
    """

    __tablename__ = "metrics"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Foreign Key
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    # Profile Completeness
    profile_completion_percentage = Column(Float, default=0.0, nullable=False)
    identity_completion = Column(Float, default=0.0, nullable=False)
    competencies_count = Column(Integer, default=0, nullable=False)
    evidence_count = Column(Integer, default=0, nullable=False)

    # Activity Metrics
    total_events = Column(Integer, default=0, nullable=False)
    events_last_30_days = Column(Integer, default=0, nullable=False)
    events_last_90_days = Column(Integer, default=0, nullable=False)
    last_activity_date = Column(DateTime(timezone=True), nullable=True)

    # Career Metrics
    job_applications_count = Column(Integer, default=0, nullable=False)
    interviews_count = Column(Integer, default=0, nullable=False)
    offers_received = Column(Integer, default=0, nullable=False)
    interviews_completed = Column(Integer, default=0, nullable=False)

    # Networking
    networking_contacts_count = Column(Integer, default=0, nullable=False)
    active_contacts = Column(Integer, default=0, nullable=False)

    # Evidence Distribution
    projects_count = Column(Integer, default=0, nullable=False)
    positions_count = Column(Integer, default=0, nullable=False)
    achievements_count = Column(Integer, default=0, nullable=False)
    certifications_count = Column(Integer, default=0, nullable=False)

    # Skill Metrics
    technical_skills_count = Column(Integer, default=0, nullable=False)
    transferable_skills_count = Column(Integer, default=0, nullable=False)
    business_skills_count = Column(Integer, default=0, nullable=False)
    average_proficiency_score = Column(Float, default=0.0, nullable=False)

    # Engagement Metrics
    logins_count = Column(Integer, default=0, nullable=False)
    logins_last_30_days = Column(Integer, default=0, nullable=False)
    average_session_duration = Column(Float, nullable=True)  # In minutes
    profile_views = Column(Integer, default=0, nullable=False)

    # File Activity
    files_uploaded = Column(Integer, default=0, nullable=False)
    files_downloaded = Column(Integer, default=0, nullable=False)

    # Performance & Scoring
    overall_profile_score = Column(Float, default=0.0, nullable=False)  # 0-100
    career_readiness_score = Column(Float, default=0.0, nullable=False)  # 0-100
    market_competitiveness_score = Column(Float, default=0.0, nullable=False)  # 0-100

    # Trends
    profile_views_trend = Column(Float, nullable=True)  # Change percentage vs last period
    engagement_trend = Column(Float, nullable=True)  # Change percentage

    # Additional Context
    extra_metadata = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    computed_at = Column(DateTime(timezone=True), nullable=True)  # When metrics were last computed

    # Relationships
    user = relationship("User", uselist=False)

    def __repr__(self):
        return f"<Metrics(id={self.id}, user_id={self.user_id}, completion={self.profile_completion_percentage}%)>"
