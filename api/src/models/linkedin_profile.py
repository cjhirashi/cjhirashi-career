"""
LinkedInProfile Model - staging content for your actual LinkedIn profile
(not the OAuth-connected posting integration - see models/linkedin_connection.py
for that). One row per user; kept as a standalone mirror of what LinkedIn's own
profile sections contain, so it's *not* deduplicated against work_history/
competencies - its purpose is to be a ready-to-copy reference when updating
the real profile on linkedin.com.
Career domain (v2) - Presencia Digital.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from database import Base


class LinkedInProfile(Base):
    __tablename__ = "linkedin_profile"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    headline = Column(String(255), nullable=True)
    about = Column(Text, nullable=True)
    profile_url = Column(String(500), nullable=True)
    location = Column(String(255), nullable=True)

    # Each: [{company, title, location, start_date, end_date, description}, ...]
    experience = Column(JSONB, nullable=True)
    # Each: [{institution, degree, field_of_study, start_date, end_date}, ...]
    education = Column(JSONB, nullable=True)

    featured_skills = Column(Text, nullable=True)  # one per line -> rendered as Markdown list
    featured_certifications = Column(Text, nullable=True)
    languages = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<LinkedInProfile(id={self.id}, user_id={self.user_id})>"
