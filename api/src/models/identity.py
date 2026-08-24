"""
Identity Model - Professional identity core (tagline, bio, UVP).
Career domain (v2) - Identity. One-to-one with User.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base


from services.id_generator import register_id_listener


class Identity(Base):
    """Core professional identity: tagline, bio summary and unique value proposition."""

    __tablename__ = "identity"

    id = Column(String(20), primary_key=True, index=True)
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    professional_tagline = Column(String(255), nullable=True)
    bio_summary = Column(Text, nullable=True)
    unique_value_proposition = Column(Text, nullable=True)

    notes = Column(Text, nullable=True)


    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<Identity(id={self.id}, user_id={self.user_id})>"

register_id_listener(Identity, "idn")
