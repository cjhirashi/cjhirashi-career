"""
StarStory Model - 60-90 second STAR-format interview stories.
Career domain (v2) - Identity.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from database import Base


class StarStory(Base):
    """A STAR-format story derived from an achievement, used in interviews."""

    __tablename__ = "star_stories"
    __table_args__ = (CheckConstraint("duration_seconds BETWEEN 60 AND 90"),)

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    title = Column(String(255), nullable=False)
    duration_seconds = Column(Integer, nullable=True)
    narrative = Column(Text, nullable=True)
    key_points = Column(JSONB, nullable=True)
    achievement_id = Column(Integer, ForeignKey("achievements.id", ondelete="SET NULL"), nullable=True)
    cross_pattern = Column(String(255), nullable=True)
    role_application = Column(Text, nullable=True)
    times_practiced = Column(Integer, default=0, nullable=True)
    active_in_interviews = Column(Boolean, default=True, nullable=True, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<StarStory(id={self.id}, title='{self.title}')>"
