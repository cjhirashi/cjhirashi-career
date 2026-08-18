"""
ApplicationInteraction Model - Communication log for an application.
Career domain (v2) - Búsqueda.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base


class ApplicationInteraction(Base):
    """An interaction (email, call, message) tied to a job application."""

    __tablename__ = "application_interactions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    application_id = Column(
        Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )

    interaction_at = Column(DateTime(timezone=True), nullable=True)
    channel = Column(String(50), nullable=True)
    content_sent = Column(Text, nullable=True)
    response_received = Column(Text, nullable=True)
    status = Column(String(50), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<ApplicationInteraction(id={self.id}, application_id={self.application_id})>"
