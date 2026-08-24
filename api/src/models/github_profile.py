"""
GitHubProfile Model - one row per user: profile copy plus the `username`
used to fetch live repository data from GitHub's public REST API (no OAuth
needed for public repos - see routes/career_digital.py's /github/repos).
Career domain (v2) - Presencia Digital.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base


from services.id_generator import register_id_listener


class GitHubProfile(Base):
    __tablename__ = "github_profile"

    id = Column(String(20), primary_key=True, index=True)
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    headline = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    readme_markdown = Column(Text, nullable=True)
    profile_url = Column(String(500), nullable=True)
    username = Column(String(255), nullable=True)

    notes = Column(Text, nullable=True)


    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<GitHubProfile(id={self.id}, username='{self.username}')>"

register_id_listener(GitHubProfile, "ghp")
