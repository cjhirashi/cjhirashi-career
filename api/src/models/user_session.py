"""
User Session Model - Session tracking and management.
"""
from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class UserSession(Base):
    """
    User session tracking for security and analytics.

    Supports:
    - Active session management
    - Multi-device tracking
    - Session-based analytics
    - Security monitoring
    """

    __tablename__ = "user_sessions"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Foreign Key
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Session Details
    session_token = Column(String(500), unique=True, nullable=False, index=True)
    session_hash = Column(String(255), nullable=False)  # Hashed for security

    # Device & Browser Information
    device_type = Column(String(100), nullable=True)  # mobile, desktop, tablet
    device_os = Column(String(100), nullable=True)  # iOS, Android, Windows, macOS, Linux
    browser_name = Column(String(100), nullable=True)  # Chrome, Firefox, Safari, etc.
    browser_version = Column(String(50), nullable=True)

    # Network Information
    ip_address = Column(String(50), nullable=False, index=True)
    user_agent = Column(String(500), nullable=True)
    country = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)

    # Session Timeline
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)

    # Session Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    was_secure = Column(Boolean, default=False, nullable=False)  # HTTPS

    # Usage Metrics
    page_views = Column(Integer, default=0, nullable=False)
    api_calls = Column(Integer, default=0, nullable=False)
    requests_count = Column(Integer, default=0, nullable=False)

    # Session Duration
    session_duration_seconds = Column(Integer, nullable=True)  # Computed at end

    # Metadata
    notes = Column(String(500), nullable=True)

    # Relationships
    user = relationship("User", back_populates="user_sessions")

    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, is_active={self.is_active})>"
