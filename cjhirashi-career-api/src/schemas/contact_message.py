"""
Schemas para contact_messages: entrada del formulario público y respuesta al Admin.
"""
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, Literal


class ContactMessageIn(BaseModel):
    """
    Payload del formulario público POST /public/contact-message.
    - name: 1-120 caracteres (se recortan espacios)
    - email: válido, hasta 255
    - message: 1-5000 caracteres
    - website: campo trampa (honeypot), se ignora si tiene contenido
    """
    name: str = Field(..., min_length=1, max_length=120)
    email: EmailStr = Field(..., max_length=255)
    message: str = Field(..., min_length=1, max_length=5000)
    website: Optional[str] = Field(default=None, max_length=255)

    def model_post_init(self, __context):
        """Recorta espacios al inicio/final."""
        self.name = self.name.strip() if self.name else ""
        self.email = self.email.strip() if self.email else ""
        self.message = self.message.strip() if self.message else ""
        if self.website:
            self.website = self.website.strip()


class ContactMessageCreated(BaseModel):
    """Respuesta 201 al crear un mensaje."""
    id: str


class ContactMessageResponse(BaseModel):
    """Respuesta GET para Admin (lista y detalle)."""
    id: str
    user_id: str
    name: str
    email: str
    message: str
    status: Literal["new", "read", "archived"]
    read_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class ContactMessageUpdate(BaseModel):
    """Payload PUT para actualizar status (Admin only)."""
    status: Literal["new", "read", "archived"] = Field(...)

    class Config:
        # Rechaza campos que no sean status
        extra = "forbid"
