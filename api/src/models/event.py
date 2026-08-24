"""
Event Model - User activity and event tracking.
"""
from sqlalchemy import Column, Integer, ForeignKey, String, Text, DateTime, Enum, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
import enum


class EventType(str, enum.Enum):
    """Type of user event."""
    PROFILE_UPDATED = "profile_updated"
    COMPETENCY_ADDED = "competency_added"
    COMPETENCY_UPDATED = "competency_updated"
    EVIDENCE_CREATED = "evidence_created"
    EVIDENCE_UPDATED = "evidence_updated"
    VACANCY_VIEWED = "vacancy_viewed"
    VACANCY_APPLIED = "vacancy_applied"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    INTERVIEW_COMPLETED = "interview_completed"
    NETWORKING_CONTACT_ADDED = "networking_contact_added"
    EXPORT_GENERATED = "export_generated"
    DOCUMENT_DOWNLOADED = "document_downloaded"
    SEARCH_PERFORMED = "search_performed"
    FILTER_APPLIED = "filter_applied"
    LOGIN = "login"
    LOGOUT = "logout"
    PASSWORD_CHANGED = "password_changed"
    OTHER = "other"


class Event(Base):
    """
    User activity event for tracking and metrics.

    Supports:
    - Activity tracking for metrics and analytics
    - User behavior analysis
    - Timeline reconstruction
    """

    __tablename__ = "events"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Foreign Key
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Event Details
    event_type = Column(Enum(EventType), nullable=False, index=True)
    event_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Related Entity
    entity_type = Column(String(100), nullable=True)  # competency, evidence, vacancy, etc.
    entity_id = Column(String(100), nullable=True)
    entity_title = Column(String(500), nullable=True)

    # Context
    context = Column(JSON, nullable=True)  # Additional context data
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)

    # Metadata
    extra_metadata = Column(JSON, nullable=True)

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="events")

    def __repr__(self):
        return f"<Event(id={self.id}, type={self.event_type}, user_id={self.user_id})>"
