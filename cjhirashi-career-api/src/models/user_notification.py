"""
Avisos in-app para Carlos (ADR-016).

Hoy el único kind es `task_turn`: una tarea o subtarea asignada al usuario
quedó desbloqueada y espera que él la ejecute. La campana del Admin lee
esta tabla; el scheduler la escribe sin sesión SPA.
"""
from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.sql import func
from database import Base
from services.id_generator import register_id_listener

NOTIFICATION_KINDS = ("task_turn",)


class UserNotification(Base):
    __tablename__ = "user_notifications"
    __table_args__ = (
        Index("ix_user_notifications_unread", "user_id", "read_at", "created_at"),
    )

    id = Column(String(20), primary_key=True)
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    kind = Column(String(40), nullable=False, default="task_turn")
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=True)
    resource_key = Column(String(80), nullable=True)
    resource_id = Column(String(40), nullable=True, index=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


register_id_listener(UserNotification, "ntf")
