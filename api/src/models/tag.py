"""
Tag Model - Generic tags usable across career-domain entities.
Career domain (v2) - Soporte.
"""
from sqlalchemy import Column, Integer, Text, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from database import Base


from services.id_generator import register_id_listener


class Tag(Base):
    """A user-defined tag, optionally scoped to an entity type, with a display color."""

    __tablename__ = "tags"
    __table_args__ = (UniqueConstraint("user_id", "tag_name"),)

    # --- Identificación (id prefijado + user_id para aislamiento) ---
    id = Column(String(20), primary_key=True, index=True)
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # --- Campos de negocio ---
    tag_name = Column(String(100), nullable=False)
    entity_type = Column(String(100), nullable=True)
    color_hex = Column(String(7), nullable=True)
    is_active = Column(Boolean, default=True, nullable=True)

    notes = Column(Text, nullable=True)


    # --- Auditoría temporal ---
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<Tag(id={self.id}, tag_name='{self.tag_name}')>"

register_id_listener(Tag, "tag")
