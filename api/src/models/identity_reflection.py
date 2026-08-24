"""
IdentityReflection Model - IKIGAI-style reflections (passion, profession, vocation, mission).
Career domain (v2) - Identity.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from database import Base


from services.id_generator import register_id_listener


class IdentityReflection(Base):
    """One reflection entry per IKIGAI dimension per user."""

    __tablename__ = "identity_reflections"
    __table_args__ = (UniqueConstraint("user_id", "dimension"),)

    id = Column(String(20), primary_key=True, index=True)
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    dimension = Column(String(50), nullable=False)  # passion | profession | vocation | mission
    content = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)

    notes = Column(Text, nullable=True)


    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<IdentityReflection(id={self.id}, dimension='{self.dimension}')>"

register_id_listener(IdentityReflection, "idr")
