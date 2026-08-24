"""
User Model - Core authentication and user management.
Implements Single Responsibility Principle.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


from services.id_generator import register_id_listener


class User(Base):
    """
    User entity for authentication and career profile management.

    This model stores user credentials and basic profile information.
    Related entities: Identity, Competencies, Evidence, JobStrategies, etc.
    """

    __tablename__ = "users"

    # Primary Key
    id = Column(String(20), primary_key=True, index=True)

    # Authentication
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # Profile Information
    full_name = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)
    professional_title = Column(String(255), nullable=True)
    photo_url = Column(String(1024), nullable=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_verified = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    #
    # NOTE: The career-domain (v2) models (Identity, Competency, Vacancy,
    # NetworkingContact, Interview, etc.) intentionally do NOT declare
    # SQLAlchemy relationship()/back_populates pairs with User. With 30
    # related tables, per-entity relationship wiring here would be high
    # maintenance and high risk (a single mismatch breaks mapper
    # configuration for the whole app on startup). Career-domain data is
    # queried directly by user_id via the dedicated routes/services
    # instead. Only base-system relationships remain wired below.
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    file_uploads = relationship("FileUpload", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="user", cascade="all, delete-orphan")
    user_sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"

register_id_listener(User, "usr")
