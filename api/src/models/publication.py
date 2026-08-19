"""
Publication Model - A content piece published on a specific platform, with metrics.
Career domain (v2) - Presencia Digital.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.sql import func
from database import Base


class Publication(Base):
    """A single publication event of a content piece on a digital platform."""

    __tablename__ = "publications"
    __table_args__ = (CheckConstraint("content_status IN ('draft', 'scheduled', 'published')"),)

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    content_piece_id = Column(
        Integer, ForeignKey("content_pieces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    platform_id = Column(
        Integer, ForeignKey("digital_platforms.id", ondelete="CASCADE"), nullable=False, index=True
    )

    published_title = Column(String(255), nullable=True)
    publication_url = Column(String(500), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    full_content = Column(Text, nullable=True)
    char_length = Column(Integer, nullable=True)
    hashtags_used = Column(Text, nullable=True)
    views = Column(Integer, nullable=True)
    likes_reactions = Column(Integer, nullable=True)
    comments = Column(Integer, nullable=True)
    shares = Column(Integer, nullable=True)
    content_status = Column(String(30), default="draft", nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<Publication(id={self.id}, content_piece_id={self.content_piece_id})>"
