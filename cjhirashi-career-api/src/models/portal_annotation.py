"""
PortalAnnotation Model - Milestone/event markers on the analytics timeline.
Annotations can mark blog posts, applications, deployments, or other events.
"""
from sqlalchemy import Column, DateTime, ForeignKey, String, Date
from sqlalchemy.sql import func
from database import Base
from services.id_generator import register_id_listener


class PortalAnnotation(Base):
    """One milestone marker: blog post, application, deploy, or other event."""

    __tablename__ = "portal_annotations"

    # --- Identificación ---
    id = Column(String(20), primary_key=True, index=True)
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    site_id = Column(String(20), ForeignKey("portal_sites.id", ondelete="CASCADE"), nullable=False, index=True)

    # --- Anotación ---
    day = Column(Date, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    kind = Column(String(50), nullable=False)  # blog_post|application|deploy|other
    ref = Column(String(255), nullable=True)  # reference id (post id, app id, etc.)

    # --- Auditoría temporal ---
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    def __repr__(self):
        return f"<PortalAnnotation(id={self.id}, title='{self.title}', kind='{self.kind}')>"


register_id_listener(PortalAnnotation, "pan")
