"""
Identity Model - Professional identity core (tagline, bio, UVP).
Career domain (v2) - Identity. One-to-one with User.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base


class Identity(Base):
    """Core professional identity: tagline, bio summary and unique value proposition."""

    __tablename__ = "identity"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    professional_tagline = Column(String(255), nullable=True)
    bio_summary = Column(Text, nullable=True)
    unique_value_proposition = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<Identity(id={self.id}, user_id={self.user_id})>"
