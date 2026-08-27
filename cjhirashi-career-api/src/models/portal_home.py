"""
PortalHome Model - copy for the public portal's Home page hero + stats
section. Deliberately lean: featured projects/publications are NOT
duplicated here - the portal reads `projects.is_featured` and
`publications.featured_on_home` directly, and the flagship achievement
block reads the single `achievements.home` row. One row per user.
Career domain (v2) - Presencia Digital.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base


from services.id_generator import register_id_listener


class PortalHome(Base):
    __tablename__ = "portal_home"

    # --- Identificación (id prefijado + user_id para aislamiento) ---
    id = Column(String(20), primary_key=True, index=True)
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    # --- Campos de negocio ---
    hero_photo_url = Column(String(1024), nullable=True)
    hero_title = Column(String(255), nullable=True)
    hero_subtitle = Column(String(500), nullable=True)
    hero_intro = Column(Text, nullable=True)

    # Up to 2 CTA buttons (text + link) - fixed slots instead of a JSON list
    # so the admin form is 2 plain fields per button, not hand-written JSON.
    # The first slot renders as the primary button, the second as secondary.
    cta1_label = Column(String(100), nullable=True)
    cta1_url = Column(String(1024), nullable=True)
    cta2_label = Column(String(100), nullable=True)
    cta2_url = Column(String(1024), nullable=True)

    # Up to 4 hero stats (name + value), same fixed-slot reasoning as the CTAs.
    stat1_label = Column(String(100), nullable=True)
    stat1_value = Column(String(50), nullable=True)
    stat2_label = Column(String(100), nullable=True)
    stat2_value = Column(String(50), nullable=True)
    stat3_label = Column(String(100), nullable=True)
    stat3_value = Column(String(50), nullable=True)
    stat4_label = Column(String(100), nullable=True)
    stat4_value = Column(String(50), nullable=True)

    notes = Column(Text, nullable=True)


    # --- Auditoría temporal ---
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<PortalHome(id={self.id}, user_id={self.user_id})>"

register_id_listener(PortalHome, "phm")
