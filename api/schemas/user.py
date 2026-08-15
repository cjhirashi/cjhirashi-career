"""
Schemas de Pydantic para modelos de usuario.
"""
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    """Schema base de usuario."""
    username: str = Field(..., min_length=3, max_length=255)
    email: EmailStr


class UserCreate(UserBase):
    """Schema para creación de usuario."""
    password: str = Field(..., min_length=6, max_length=255)


class UserResponse(UserBase):
    """Schema para respuesta de usuario (sin password)."""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    """Schema para request de login."""
    username: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=1, max_length=255)


class TokenResponse(BaseModel):
    """Schema para respuesta de token JWT."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Tiempo de expiración en segundos")
    user: UserResponse
