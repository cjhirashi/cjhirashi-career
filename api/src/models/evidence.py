"""
Evidence Model - Career evidence and accomplishments.
Stores projects, positions, achievements, STAR cases.
"""
from sqlalchemy import Column, Integer, ForeignKey, String, Text, DateTime, Enum, Boolean, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
import enum


class EvidenceType(str, enum.Enum):
    """Type of evidence."""
    PROJECT = "project"  # Work or personal project
    POSITION = "position"  # Job position or role
    ACHIEVEMENT = "achievement"  # Award, certification, recognition
    CASE_STUDY = "case_study"  # STAR method case study
    PUBLICATION = "publication"  # Article, blog post, paper
    CERTIFICATION = "certification"  # Course completion, license
    VOLUNTEER = "volunteer"  # Volunteer work
    OTHER = "other"  # Miscellaneous evidence


class Evidence(Base):
    """
    Career evidence supporting competencies and achievements.

    Supports:
    - Projects (personal, work, open-source)
    - Positions (job roles with responsibilities)
    - Achievements (awards, recognitions)
    - STAR cases (Situation, Task, Action, Result)
    - Publications and certifications
    - Volunteer work
    """

    __tablename__ = "evidence"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Foreign Key
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Evidence Details
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    evidence_type = Column(Enum(EvidenceType), nullable=False, index=True)
    category = Column(String(100), nullable=True, index=True)

    # Organization/Company
    organization = Column(String(255), nullable=True, index=True)
    position_title = Column(String(255), nullable=True)

    # Timeline
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    is_current = Column(Boolean, default=False, nullable=False)

    # Project/Achievement Details
    outcome = Column(Text, nullable=True)
    impact = Column(Text, nullable=True)
    metrics = Column(JSON, nullable=True)  # Quantifiable results

    # STAR Method (Situation, Task, Action, Result)
    situation = Column(Text, nullable=True)
    task = Column(Text, nullable=True)
    action = Column(Text, nullable=True)
    result = Column(Text, nullable=True)

    # Skills/Competencies Demonstrated
    skills_demonstrated = Column(String(1000), nullable=True)  # Comma-separated skill IDs or names

    # External Links
    project_url = Column(String(500), nullable=True)
    portfolio_url = Column(String(500), nullable=True)
    certificate_url = Column(String(500), nullable=True)

    # Files/Attachments
    attachment_ids = Column(String(1000), nullable=True)  # Comma-separated file IDs

    # Visibility & Publishing
    is_public = Column(Boolean, default=False, nullable=False, index=True)
    is_featured = Column(Boolean, default=False, nullable=False, index=True)
    priority = Column(Integer, default=0, nullable=False)

    # SEO & Discovery
    tags = Column(String(500), nullable=True)
    keywords = Column(String(500), nullable=True)

    # Verification
    is_verified = Column(Boolean, default=False, nullable=False)
    verified_by = Column(String(255), nullable=True)

    # Metadata
    metadata = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="evidence_list")

    def __repr__(self):
        return f"<Evidence(id={self.id}, title='{self.title}', type={self.evidence_type})>"
