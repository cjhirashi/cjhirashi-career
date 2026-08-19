"""
RoleNarrative Model - Reusable narratives tailored to a target role/context.
Career domain (v2) - Búsqueda.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base


class RoleNarrative(Base):
    """A narrative (elevator pitch, cover-letter angle, interview framing, etc.)."""

    __tablename__ = "role_narratives"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    target_role_id = Column(Integer, ForeignKey("target_roles.id", ondelete="SET NULL"), nullable=True)

    title = Column(String(255), nullable=False)
    usage_context = Column(String(100), nullable=True, index=True)
    full_narrative = Column(Text, nullable=True)
    key_points = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<RoleNarrative(id={self.id}, title='{self.title}')>"
