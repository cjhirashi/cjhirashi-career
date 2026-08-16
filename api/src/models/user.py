"""
User Model - Core authentication and user management.
Implements Single Responsibility Principle.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    """
    User entity for authentication and career profile management.

    This model stores user credentials and basic profile information.
    Related entities: Identity, Competencies, Evidence, JobStrategies, etc.
    """

    __tablename__ = "users"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Authentication
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # Profile Information
    full_name = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)
    professional_title = Column(String(255), nullable=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_verified = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    identity = relationship("Identity", uselist=False, back_populates="user", cascade="all, delete-orphan")
    competencies = relationship("Competency", back_populates="user", cascade="all, delete-orphan")
    evidence_list = relationship("Evidence", back_populates="user", cascade="all, delete-orphan")
    job_strategies = relationship("JobStrategy", back_populates="user", cascade="all, delete-orphan")
    vacancies = relationship("Vacancy", back_populates="user", cascade="all, delete-orphan")
    networking_contacts = relationship("NetworkingContact", back_populates="user", cascade="all, delete-orphan")
    interviews = relationship("Interview", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    file_uploads = relationship("FileUpload", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="user", cascade="all, delete-orphan")
    user_sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
