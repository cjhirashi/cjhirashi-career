"""
PortalHome Model - copy for the public portal's Home page hero section only.
Deliberately lean: featured projects/publications are NOT duplicated here -
the portal reads `projects.is_featured` and `publications.featured_on_home`
directly. One row per user.
Career domain (v2) - Presencia Digital.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base


class PortalHome(Base):
    __tablename__ = "portal_home"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    hero_title = Column(String(255), nullable=True)
    hero_subtitle = Column(String(500), nullable=True)
    hero_intro = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<PortalHome(id={self.id}, user_id={self.user_id})>"
