"""
Competency Model - Professional skills and competencies.
Classifies: technical, transferable, business.
"""
from sqlalchemy import Column, Integer, ForeignKey, String, Text, DateTime, Enum, Float, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
import enum


class CompetencyType(str, enum.Enum):
    """Competency classification types."""
    TECHNICAL = "technical"  # Hard skills: Python, SQL, AWS, etc.
    TRANSFERABLE = "transferable"  # Soft skills: communication, leadership, etc.
    BUSINESS = "business"  # Business skills: negotiation, project management, etc.


class CompetencyLevel(str, enum.Enum):
    """Proficiency levels."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class Competency(Base):
    """
    Professional competency or skill.

    Supports:
    - Technical skills (programming languages, tools, frameworks)
    - Transferable skills (soft skills applicable across roles)
    - Business skills (domain knowledge, industry expertise)
    """

    __tablename__ = "competencies"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Foreign Key
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Competency Details
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    competency_type = Column(Enum(CompetencyType), nullable=False, index=True)
    proficiency_level = Column(Enum(CompetencyLevel), default=CompetencyLevel.INTERMEDIATE, nullable=False)

    # Proficiency Score (0-100)
    proficiency_score = Column(Float, default=50.0, nullable=False)

    # Category for organization
    category = Column(String(100), nullable=True, index=True)

    # Endorsement/Validation
    endorsement_count = Column(Integer, default=0, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    # Experience
    years_of_experience = Column(Float, nullable=True)
    last_used_date = Column(DateTime(timezone=True), nullable=True)

    # Certification/Evidence Links
    certification_url = Column(String(500), nullable=True)
    evidence_ids = Column(String(1000), nullable=True)  # Comma-separated Evidence IDs

    # SEO & Discovery
    keywords = Column(String(500), nullable=True)

    # Metadata
    is_featured = Column(Boolean, default=False, nullable=False, index=True)
    priority = Column(Integer, default=0, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="competencies")

    def __repr__(self):
        return f"<Competency(id={self.id}, name='{self.name}', type={self.competency_type})>"
