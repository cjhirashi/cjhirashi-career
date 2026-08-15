"""
Schemas de Pydantic para validación y serialización.
"""
from schemas.user import UserCreate, UserResponse, LoginRequest, TokenResponse
from schemas.document import (
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
    DocumentListResponse
)

__all__ = [
    "UserCreate",
    "UserResponse",
    "LoginRequest",
    "TokenResponse",
    "DocumentCreate",
    "DocumentUpdate",
    "DocumentResponse",
    "DocumentListResponse"
]
