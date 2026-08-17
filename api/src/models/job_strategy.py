"""
Job Strategy Model - Career planning and job search strategies.
"""
from sqlalchemy import Column, Integer, ForeignKey, String, Text, DateTime, Enum, Boolean, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
import enum


class JobStrategyStatus(str, enum.Enum):
    """Status of a job strategy."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class JobStrategy(Base):
    """
    Career job search and positioning strategy.

    Supports:
    - Target industries and roles
    - Companies of interest
    - Search strategy and approach
    - Timeline and goals
    """

    __tablename__ = "job_strategies"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Foreign Key
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Strategy Details
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(Enum(JobStrategyStatus), default=JobStrategyStatus.ACTIVE, nullable=False, index=True)

    # Target Position
    target_job_title = Column(String(255), nullable=True)
    target_industry = Column(String(255), nullable=True, index=True)
    target_role_level = Column(String(100), nullable=True)  # entry, mid, senior, lead, etc.
    target_salary_min = Column(Integer, nullable=True)
    target_salary_max = Column(Integer, nullable=True)

    # Geographic Preferences
    preferred_locations = Column(String(500), nullable=True)
    remote_preference = Column(String(100), nullable=True)  # hybrid, remote, on-site

    # Companies of Interest
    target_companies = Column(String(1000), nullable=True)  # Comma-separated company names
    company_urls = Column(String(2000), nullable=True)

    # Strategy & Approach
    strategy_approach = Column(Text, nullable=True)
    key_focus_areas = Column(String(500), nullable=True)
    differentiators = Column(Text, nullable=True)  # What makes you unique for this role

    # Timeline
    start_date = Column(DateTime(timezone=True), nullable=True)
    target_date = Column(DateTime(timezone=True), nullable=True)

    # Metrics & Tracking
    applications_count = Column(Integer, default=0, nullable=False)
    interviews_count = Column(Integer, default=0, nullable=False)
    offers_count = Column(Integer, default=0, nullable=False)

    # Notes
    notes = Column(Text, nullable=True)
    extra_metadata = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="job_strategies")

    def __repr__(self):
        return f"<JobStrategy(id={self.id}, title='{self.title}', status={self.status})>"
