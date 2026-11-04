"""
Recurso Admin para contact-messages (RF-006).

CRUD router construido con build_crud_router: solo status es editable en PUT.
Requiere autenticación; aislado por user_id (solo el dueño del portafolio).
"""
from fastapi import APIRouter
from sqlalchemy import DateTime, func
from datetime import datetime

from models.contact_message import ContactMessage
from schemas.contact_message import (
    ContactMessageResponse,
    ContactMessageUpdate,
)
from routes.career_common import build_crud_router

# ============================================================================
# Router para contact-messages
# ============================================================================

router = APIRouter()

# Schema para crear (no se usa en Admin, pero build_crud_router lo requiere)
class ContactMessageCreateForAdmin(ContactMessageResponse):
    """Dummy schema para CREATE (no usado en Admin)."""
    pass


# Construir el CRUD router
router.include_router(
    build_crud_router(
        prefix="/contact-messages",
        tags=["Admin - Contact Messages"],
        model=ContactMessage,
        create_schema=ContactMessageCreateForAdmin,
        update_schema=ContactMessageUpdate,
        response_schema=ContactMessageResponse,
        entity_name="contact message",
        vectorize=False,  # No indexar en Qdrant (no es contenido para el agente)
    )
)
