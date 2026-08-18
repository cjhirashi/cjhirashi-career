"""
ContentPiece Model - Blog/content pieces authored by the user.
Career domain (v2) - Presencia Digital.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from database import Base


class ContentPiece(Base):
    """A piece of content (article, post) that may be published to multiple platforms."""

    __tablename__ = "content_pieces"
    __table_args__ = (
        CheckConstraint("status IN ('draft', 'scheduled', 'published')"),
        UniqueConstraint("user_id", "slug"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    related_project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    related_achievement_id = Column(Integer, ForeignKey("achievements.id", ondelete="SET NULL"), nullable=True)
    related_competency_id = Column(Integer, ForeignKey("competencies.id", ondelete="SET NULL"), nullable=True)

    title = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=True)
    excerpt = Column(String(500), nullable=True)
    body_content = Column(Text, nullable=True)
    content_type = Column(String(50), nullable=True)
    thematic_pillar = Column(String(100), nullable=True)
    tags = Column(JSONB, nullable=True)
    status = Column(String(30), default="draft", nullable=True, index=True)
    reading_minutes = Column(Integer, nullable=True)
    featured_on_home = Column(Boolean, default=False, nullable=True)
    scheduled_publish_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<ContentPiece(id={self.id}, title='{self.title}')>"
