"""
LinkedInPost Model - audit log of posts published through the admin panel's
LinkedIn integration (not a source of truth - LinkedIn itself is; this is
just history so the "Publicar" page can show what went out and when).
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base


class LinkedInPost(Base):
    __tablename__ = "linkedin_posts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    text = Column(Text, nullable=False)
    linkedin_post_urn = Column(String(255), nullable=True)
    published_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<LinkedInPost(id={self.id}, urn='{self.linkedin_post_urn}')>"
