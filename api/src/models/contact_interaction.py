"""
ContactInteraction Model - Communication log with a networking contact.
Career domain (v2) - Búsqueda.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base


class ContactInteraction(Base):
    """An interaction with a networking contact, optionally tied to an opportunity."""

    __tablename__ = "contact_interactions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    contact_id = Column(
        Integer, ForeignKey("networking_contacts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    related_vacancy_id = Column(Integer, ForeignKey("vacancies.id", ondelete="SET NULL"), nullable=True)

    interaction_at = Column(DateTime(timezone=True), nullable=True)
    channel = Column(String(50), nullable=True)
    content_sent = Column(Text, nullable=True)
    response_received = Column(Text, nullable=True)
    status = Column(String(50), nullable=True)
    generated_opportunity = Column(Boolean, default=False, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<ContactInteraction(id={self.id}, contact_id={self.contact_id})>"
