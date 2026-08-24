"""
Pydantic schemas for the LinkedIn integration (connection status, posting).
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# ============================================================================
# Conexión — respuestas de estado y autorización
# ============================================================================

class LinkedInStatusResponse(BaseModel):
    connected: bool
    member_name: Optional[str] = None
    member_email: Optional[str] = None
    profile_picture_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    notes: Optional[str] = None


class LinkedInConnectResponse(BaseModel):
    authorize_url: str
    notes: Optional[str] = None


# ============================================================================
# Publicaciones — respuestas
# ============================================================================

class LinkedInPostResponse(BaseModel):
    id: str
    text: str
    image_url: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    linkedin_post_urn: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    created_at: datetime
    notes: Optional[str] = None

    class Config:
        from_attributes = True
