"""
LinkedInPost Model - audit log + scheduling queue for posts published (or
scheduled to be published) through the admin panel's LinkedIn integration.

LinkedIn's API has no native scheduling (no scheduled_at field, every post
created via the API goes out immediately) - `status`/`scheduled_at` here are
what the background scheduler in app.py polls to publish a post at the
right time itself. This table is not LinkedIn's source of truth once a
post is live; it's history plus the not-yet-published queue.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base


class LinkedInPostStatus:
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"


from services.id_generator import register_id_listener


class LinkedInPost(Base):
    __tablename__ = "linkedin_posts"

    # --- Identificación (id prefijado + user_id para aislamiento) ---
    id = Column(String(20), primary_key=True, index=True)
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # --- Campos de negocio ---
    text = Column(Text, nullable=False)
    image_url = Column(String(1024), nullable=True)  # our own MinIO copy, for display/re-upload at publish time
    status = Column(String(20), nullable=False, default=LinkedInPostStatus.PUBLISHED)
    error_message = Column(Text, nullable=True)

    linkedin_post_urn = Column(String(255), nullable=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)


    # --- Auditoría temporal ---
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<LinkedInPost(id={self.id}, status='{self.status}')>"

register_id_listener(LinkedInPost, "lnp")
