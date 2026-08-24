"""
ApplicationInteraction Model - Communication log for an application.
Career domain (v2) - Búsqueda.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base


from services.id_generator import register_id_listener


class ApplicationInteraction(Base):
    """An interaction (email, call, message) tied to a job application."""

    __tablename__ = "application_interactions"

    # --- Identificación (id prefijado + user_id para aislamiento) ---
    id = Column(String(20), primary_key=True, index=True)
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    # --- Campos de negocio ---
    application_id = Column(String(20), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )

    interaction_at = Column(DateTime(timezone=True), nullable=True)
    channel = Column(String(50), nullable=True)
    content_sent = Column(Text, nullable=True)
    response_received = Column(Text, nullable=True)
    status = Column(String(50), nullable=True)

    notes = Column(Text, nullable=True)


    # --- Auditoría temporal ---
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<ApplicationInteraction(id={self.id}, application_id={self.application_id})>"

register_id_listener(ApplicationInteraction, "ain")
