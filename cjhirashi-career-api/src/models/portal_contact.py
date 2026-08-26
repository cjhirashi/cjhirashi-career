"""
PortalContact Model - copy for the public portal's Contact page AND the
site-wide footer links. LinkedIn/GitHub links are read from linkedin_profile/
github_profile, not duplicated here - `footer_links` covers everything else
(resume download, X/Twitter, a second email, etc.). One row per user.
Career domain (v2) - Presencia Digital.
"""
from sqlalchemy import Column, Integer, Text, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from database import Base


from services.id_generator import register_id_listener


class PortalContact(Base):
    __tablename__ = "portal_contact"

    # --- Identificación (id prefijado + user_id para aislamiento) ---
    id = Column(String(20), primary_key=True, index=True)
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    # --- Campos de negocio ---
    contact_email = Column(String(255), nullable=True)
    whatsapp = Column(String(50), nullable=True)
    location = Column(String(255), nullable=True)
    availability_status = Column(String(50), nullable=True)
    preferred_contact_method = Column(String(100), nullable=True)
    # [{label, url}, ...] - anything else that belongs in the portal's footer
    # beyond the LinkedIn/GitHub links (which come from their own tables).
    footer_links = Column(JSONB, nullable=True)

    notes = Column(Text, nullable=True)


    # --- Auditoría temporal ---
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<PortalContact(id={self.id}, user_id={self.user_id})>"

register_id_listener(PortalContact, "pco")
