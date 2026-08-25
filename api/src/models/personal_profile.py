"""
PersonalProfile Model - biographical facts used as a reference by the
career manager (legal name, date of birth, contact, location).

Distinct from `identity` (tagline / bio / UVP). One-to-one with User.
Career domain (v2) - Identidad Profesional.
"""
from sqlalchemy import Column, Date, DateTime, ForeignKey, String, Text
from sqlalchemy.sql import func

from database import Base
from services.id_generator import register_id_listener


class PersonalProfile(Base):
    """Singleton biographical card: who Carlos is as a person, not the professional narrative."""

    __tablename__ = "personal_profile"

    id = Column(String(20), primary_key=True, index=True)
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    full_name = Column(String(255), nullable=False)
    preferred_name = Column(String(255), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    nationality = Column(String(100), nullable=True)
    city = Column(String(255), nullable=True)
    country = Column(String(100), nullable=True)
    phone = Column(String(40), nullable=True)
    email = Column(String(255), nullable=True)
    languages = Column(Text, nullable=True)
    work_authorization = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<PersonalProfile(id={self.id}, user_id={self.user_id})>"


register_id_listener(PersonalProfile, "psp")
