"""
Networking Model - Professional networking contacts.
"""
from sqlalchemy import Column, Integer, ForeignKey, String, Text, DateTime, Boolean, Enum, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
import enum


class ContactStatus(str, enum.Enum):
    """Contact relationship status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"


class RelationshipType(str, enum.Enum):
    """Type of professional relationship."""
    MENTOR = "mentor"
    MENTEE = "mentee"
    COLLEAGUE = "colleague"
    FRIEND = "friend"
    CLIENT = "client"
    VENDOR = "vendor"
    RECRUITER = "recruiter"
    INDUSTRY_CONTACT = "industry_contact"
    OTHER = "other"


class NetworkingContact(Base):
    """
    Professional networking contact.

    Supports:
    - Contact information and relationship details
    - Interaction history and follow-ups
    - Value exchange tracking
    """

    __tablename__ = "networking_contacts"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Foreign Key
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Contact Information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(20), nullable=True)

    # Professional Details
    professional_title = Column(String(255), nullable=True)
    company = Column(String(255), nullable=True, index=True)
    industry = Column(String(100), nullable=True)
    location = Column(String(255), nullable=True)

    # Relationship
    relationship_type = Column(Enum(RelationshipType), nullable=False, index=True)
    status = Column(Enum(ContactStatus), default=ContactStatus.ACTIVE, nullable=False, index=True)
    relationship_strength = Column(Integer, nullable=True)  # 1-5 scale

    # Connection Date
    connected_date = Column(DateTime(timezone=True), nullable=True)
    connection_source = Column(String(255), nullable=True)  # Where you met (LinkedIn, conference, etc.)

    # Communication & Follow-up
    last_contact_date = Column(DateTime(timezone=True), nullable=True)
    next_follow_up_date = Column(DateTime(timezone=True), nullable=True)
    follow_up_frequency = Column(String(100), nullable=True)  # weekly, monthly, quarterly, etc.

    # Social Links
    linkedin_url = Column(String(500), nullable=True)
    twitter_handle = Column(String(255), nullable=True)
    website_url = Column(String(500), nullable=True)

    # Communication Preferences
    preferred_contact_method = Column(String(100), nullable=True)  # email, phone, linkedin, etc.
    communication_notes = Column(Text, nullable=True)

    # Value & Opportunities
    shared_interests = Column(String(500), nullable=True)  # Comma-separated interests
    potential_opportunities = Column(Text, nullable=True)  # Collaboration, mentoring, etc.
    how_you_can_help = Column(Text, nullable=True)

    # Interaction History
    interaction_count = Column(Integer, default=0, nullable=False)
    last_interaction = Column(DateTime(timezone=True), nullable=True)

    # Notes
    notes = Column(Text, nullable=True)
    tags = Column(String(500), nullable=True)  # Comma-separated tags for organization

    # Metadata
    extra_metadata = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="networking_contacts")

    def __repr__(self):
        return f"<NetworkingContact(id={self.id}, name='{self.first_name} {self.last_name}', company='{self.company}')>"
