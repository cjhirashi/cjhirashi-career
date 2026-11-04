"""
Lógica de negocio para mensajes de contacto del portafolio.

- Guardar mensaje (RF-001, RF-002)
- Honeypot silencioso (RF-003)
- Crear aviso para el Admin (RF-005)
- Guardar primero, avisar después (fallo del aviso no pierde el mensaje)
"""
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from models.contact_message import ContactMessage
from models.user_notification import UserNotification

logger = logging.getLogger(__name__)


class ContactMessageService:
    """Servicio para gestionar mensajes de contacto."""

    async def save_contact_message(
        self,
        db: AsyncSession,
        user_id: str,
        message_data: dict,
    ) -> Optional[str]:
        """
        Guarda un mensaje de contacto y crea un aviso.

        Estrategia: guardar primero (commit), avisar después (fallo no pierde el mensaje).

        Args:
            db: sesión async de BD
            user_id: propietario del portafolio (PUBLIC_PORTAL_USER_ID)
            message_data: dict con name, email, message, website

        Returns:
            id del mensaje (ej. "cmg-1") o None si fue honeypot
        """
        # ===== Honeypot: detecta bots (RF-003) =====
        website = (message_data.get("website") or "").strip()
        if website:
            # Bot detectado: silencio total, no guardar ni avisar
            logger.info("Contact form honeypot triggered (website field filled)")
            return None

        # ===== Recortar espacios (RF-001) =====
        name = (message_data.get("name") or "").strip()
        email = (message_data.get("email") or "").strip()
        message_text = (message_data.get("message") or "").strip()

        # ===== Crear fila de contact_message (RF-002) =====
        contact_msg = ContactMessage(
            user_id=user_id,
            name=name,
            email=email,
            message=message_text,
            status="new",
        )
        db.add(contact_msg)
        await db.flush()  # Genera el id prefijado
        msg_id = contact_msg.id

        try:
            await db.commit()
        except Exception:
            await db.rollback()
            logger.exception("Failed to save contact message")
            raise

        # ===== Crear aviso (RF-005) =====
        # Si falla, se registra pero no revierte la fila (guardar primero)
        try:
            await self._create_notification(db, user_id, name, msg_id)
        except Exception:
            logger.exception("Failed to create notification for contact message %s", msg_id)
            # No relanzar: el mensaje está guardado

        return msg_id

    async def _create_notification(
        self,
        db: AsyncSession,
        user_id: str,
        sender_name: str,
        message_id: str,
    ) -> None:
        """
        Crea un aviso UserNotification para el Admin.

        Se ejecuta después de confirmar el mensaje en BD.
        """
        notification = UserNotification(
            user_id=user_id,
            kind="contact_message",
            title=f"Mensaje de {sender_name}",
            body=None,  # El texto está en contact_messages, no se duplica
            resource_key="contact-messages",
            resource_id=message_id,
        )
        db.add(notification)
        await db.flush()
        await db.commit()
