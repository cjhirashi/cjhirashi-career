"""
RoleNarrative Model - Reusable narratives tailored to a target role/context.
Career domain (v2) - Búsqueda.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base


from services.id_generator import register_id_listener


class RoleNarrative(Base):
    """A narrative (elevator pitch, cover-letter angle, interview framing, etc.)."""

    __tablename__ = "role_narratives"

    # --- Identificación (id prefijado + user_id para aislamiento) ---
    id = Column(String(20), primary_key=True, index=True)
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    # --- Campos de negocio ---
    target_role_id = Column(String(20), ForeignKey("target_roles.id", ondelete="SET NULL"), nullable=True)

    title = Column(String(255), nullable=False)
    usage_context = Column(String(100), nullable=True, index=True)
    full_narrative = Column(Text, nullable=True)
    key_points = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=True)

    notes = Column(Text, nullable=True)


    # --- Auditoría temporal ---
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<RoleNarrative(id={self.id}, title='{self.title}')>"

register_id_listener(RoleNarrative, "rna")
