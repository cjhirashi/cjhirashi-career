"""
PortalAbout Model - copy for the public portal's "Sobre Mí" page that isn't
already covered by other tables: no bio/tagline (already in `identity`),
no experience/skills/certifications (already in work_history/competencies/
certifications). Just the hero photo. One row per user.
Career domain (v2) - Presencia Digital.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from database import Base
from sqlalchemy.sql import func


class PortalAbout(Base):
    __tablename__ = "portal_about"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    photo_url = Column(String(1024), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<PortalAbout(id={self.id}, user_id={self.user_id})>"
