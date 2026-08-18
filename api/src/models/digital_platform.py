"""
DigitalPlatform Model - Digital presence platforms (LinkedIn, GitHub, etc.).
Career domain (v2) - Presencia Digital.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.sql import func
from database import Base


class DigitalPlatform(Base):
    """A digital platform used for professional presence and content distribution."""

    __tablename__ = "digital_platforms"
    __table_args__ = (
        CheckConstraint(
            "platform_name IN ('linkedin', 'github', 'kaggle', 'portfolio_web', 'medium', "
            "'twitter', 'other')"
        ),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    platform_name = Column(String(50), nullable=True)
    profile_url = Column(String(500), nullable=True)
    profile_status = Column(String(30), nullable=True)
    platform_strategy = Column(Text, nullable=True)
    followers_count = Column(Integer, nullable=True)
    is_active_in_search = Column(Boolean, default=True, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<DigitalPlatform(id={self.id}, platform_name='{self.platform_name}')>"
