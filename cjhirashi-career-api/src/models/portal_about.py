"""
PortalAbout Model - copy for the public portal's "Sobre Mí" page. One row
per user.
Career domain (v2) - Presencia Digital.

NOTE (checklist Paulina #12): photo_url + name alone are insufficient for a
public "About me" page, so bio_text/headline/timeline_milestones were added
here even though a bio/tagline already exists in `identity` - that one is
the internal narrative built from Reflexiones IKIGAI; this is portal-facing
copy the user may want to phrase differently for a public audience.
"""
from sqlalchemy import Column, Integer, Text, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from database import Base
from sqlalchemy.sql import func


from services.id_generator import register_id_listener


class PortalAbout(Base):
    __tablename__ = "portal_about"

    # --- Identificación (id prefijado + user_id para aislamiento) ---
    id = Column(String(20), primary_key=True, index=True)
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    # --- Campos de negocio ---
    photo_url = Column(String(1024), nullable=True)
    name = Column(String(255), nullable=True)
    headline = Column(String(255), nullable=True)
    bio_text = Column(Text, nullable=True)
    # Lista de hitos [{date, title, description}, ...] para una línea de
    # tiempo en la página pública.
    timeline_milestones = Column(JSONB, nullable=True)

    notes = Column(Text, nullable=True)


    # --- Auditoría temporal ---
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<PortalAbout(id={self.id}, user_id={self.user_id})>"

register_id_listener(PortalAbout, "pab")
