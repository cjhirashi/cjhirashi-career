"""
Recurso Admin `contact-messages` (SPEC-0011 RF-006): listar, leer, cambiar el
estado y borrar los mensajes del formulario de contacto del portafolio.

Sin POST: los mensajes solo entran por `POST /public/contact-message`.
Solo `status` es editable; `read_at` lo fija el modelo.
"""
from fastapi import APIRouter

from models.contact_message import ContactMessage
from routes.career_common import build_crud_router
from schemas.contact_message import ContactMessageResponse, ContactMessageUpdate

router = APIRouter(prefix="/career")

router.include_router(
    build_crud_router(
        prefix="/contact-messages",
        tags=["Admin - Contact Messages"],
        model=ContactMessage,
        create_schema=None,
        update_schema=ContactMessageUpdate,
        response_schema=ContactMessageResponse,
        entity_name="contact message",
        vectorize=False,
    )
)
