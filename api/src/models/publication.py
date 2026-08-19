"""
Publication Model - a blog/content post (feeds the portal's Blog page via
`featured_on_home`), previously split across `content_pieces` +
`digital_platforms` + this table. Merged into one standalone table: `platform`
is now free text instead of a FK to a removed `digital_platforms` table, and
the authoring fields content_pieces used to hold live here directly.
Career domain (v2) - Presencia Digital.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.sql import func
from database import Base


class Publication(Base):
    __tablename__ = "publications"
    __table_args__ = (CheckConstraint("status IN ('draft', 'scheduled', 'published')"),)

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    related_project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)

    title = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=True)
    excerpt = Column(String(500), nullable=True)
    body_content = Column(Text, nullable=True)  # Markdown
    content_type = Column(String(50), nullable=True)
    tags = Column(Text, nullable=True)
    image_url = Column(String(1024), nullable=True)

    platform = Column(String(100), nullable=True)  # free text: "LinkedIn", "Blog propio", "Medium", ...
    publication_url = Column(String(500), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)

    views = Column(Integer, nullable=True)
    likes_reactions = Column(Integer, nullable=True)
    comments = Column(Integer, nullable=True)
    shares = Column(Integer, nullable=True)

    status = Column(String(30), default="draft", nullable=True, index=True)
    reading_minutes = Column(Integer, nullable=True)
    featured_on_home = Column(Boolean, default=False, nullable=True, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<Publication(id={self.id}, title='{self.title}')>"
