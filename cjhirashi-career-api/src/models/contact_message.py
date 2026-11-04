"""
ContactMessage Model - mensajes del formulario de contacto del portafolio.

Los visitantes anónimos envían mensajes que se guardan con estado de lectura
(new/read/archived) para que el Admin (Carlos) los lea en su panel. No se
guarda IP ni cabeceras; IP solo vive en memoria para el límite de frecuencia.

Dominio: Presencia Digital (portafolio público).
"""
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index, CheckConstraint
from sqlalchemy.orm import validates
from sqlalchemy.sql import func
from database import Base
from services.id_generator import register_id_listener


class ContactMessage(Base):
    __tablename__ = "contact_messages"
    __table_args__ = (
        CheckConstraint("status IN ('new', 'read', 'archived')", name="ck_contact_message_status"),
        Index("ix_contact_messages_user_status_created", "user_id", "status", "created_at"),
    )

    # --- Identificación (id prefijado + user_id para aislamiento) ---
    id = Column(String(20), primary_key=True, index=True)
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # --- Campos del formulario ---
    name = Column(String(120), nullable=False)
    email = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)

    # --- Estado de lectura ---
    status = Column(String(20), nullable=False, default="new", index=True)
    read_at = Column(DateTime(timezone=True), nullable=True)

    # --- Auditoría temporal ---
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    @validates("status")
    def _stamp_read_at(self, _key, value):
        # El primer paso a read/archived fija read_at; volver a new no lo borra.
        if value in ("read", "archived") and self.read_at is None:
            self.read_at = datetime.now(timezone.utc)
        return value

    def __repr__(self):
        return f"<ContactMessage(id={self.id}, user_id={self.user_id}, status={self.status})>"


register_id_listener(ContactMessage, "cmg")
