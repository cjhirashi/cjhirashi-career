"""
NetworkingContact Model - Professional network contacts.
Career domain (v2) - Búsqueda.

NOTE: Replaces the legacy `models/networking.py` (deleted), whose columns
did not match the real `networking_contacts` table.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.sql import func
from database import Base


from services.id_generator import register_id_listener


class NetworkingContact(Base):
    """A professional contact used in the job search / networking strategy."""

    __tablename__ = "networking_contacts"
    __table_args__ = (
        CheckConstraint(
            "role_category IN ('data_director', 'automation_ai_peer', 'manager_team_lead', "
            "'specialized_recruiter', 'target_company_lead')"
        ),
        CheckConstraint(
            "contact_status IN ('pending', 'contacted', 'following_up', 'converted')"
        ),
    )

    id = Column(String(20), primary_key=True, index=True)
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    role_title = Column(String(255), nullable=True)
    company_or_specialty = Column(String(255), nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    email = Column(String(255), nullable=True)
    role_category = Column(String(50), nullable=True, index=True)
    contact_status = Column(String(30), default="pending", nullable=True, index=True)
    how_originated = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<NetworkingContact(id={self.id}, name='{self.name}')>"

register_id_listener(NetworkingContact, "nwc")
