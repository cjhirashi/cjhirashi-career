"""
Pydantic schemas for User and Authentication.
Request/Response validation and serialization.
"""
from pydantic import BaseModel, EmailStr, Field, constr, field_validator
from typing import Optional
from datetime import datetime


# ============================================================================
# Base Schemas
# ============================================================================

class UserBase(BaseModel):
    """Base user schema with common fields."""
    username: str = Field(..., min_length=3, max_length=255, description="Unique username")
    email: EmailStr = Field(..., description="User email address")
    full_name: Optional[str] = Field(None, max_length=255, description="Full name")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    country: Optional[str] = Field(None, max_length=100, description="Country")
    professional_title: Optional[str] = Field(None, max_length=255, description="Professional title")
    photo_url: Optional[str] = Field(None, max_length=1024, description="Profile photo URL")


# ============================================================================
# User CRUD Schemas
# ============================================================================

class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: constr(min_length=8, max_length=255) = Field(..., description="Password (min 8 characters)")


class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    full_name: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    professional_title: Optional[str] = Field(None, max_length=255)
    photo_url: Optional[str] = Field(None, max_length=1024)


class UserResponse(UserBase):
    """User response schema (safe to send to client)."""
    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserProfileResponse(UserResponse):
    """Extended user profile response with statistics."""
    competencies_count: Optional[int] = 0
    evidence_count: Optional[int] = 0
    networking_contacts_count: Optional[int] = 0


# ============================================================================
# Authentication Schemas
# ============================================================================

class LoginRequest(BaseModel):
    """Login request with credentials."""
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="User password")


class LoginResponse(BaseModel):
    """Successful login response with tokens."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: Optional[str] = Field(None, description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration in seconds")
    user: UserResponse = Field(..., description="User information")


class TokenRefreshRequest(BaseModel):
    """Request to refresh access token."""
    refresh_token: str = Field(..., description="Valid refresh token")


class TokenRefreshResponse(BaseModel):
    """Response with refreshed access token."""
    access_token: str = Field(..., description="New JWT access token")
    token_type: str = Field(default="bearer")
    expires_in: int = Field(..., description="Token expiration in seconds")


class LogoutResponse(BaseModel):
    """Logout response."""
    message: str = Field(default="Logout successful")


# ============================================================================
# Password Management Schemas
# ============================================================================

class PasswordChangeRequest(BaseModel):
    """Request to change password."""
    current_password: str = Field(..., description="Current password")
    new_password: constr(min_length=8, max_length=255) = Field(..., description="New password (must be different from current)")

    @field_validator('new_password')
    @classmethod
    def new_password_must_differ(cls, v, info):
        """Ensure new password is different from current password."""
        if info.data.get('current_password') == v:
            raise ValueError('New password must be different from current password')
        return v


class PasswordResetRequest(BaseModel):
    """Request to reset password."""
    email: EmailStr = Field(..., description="User email address")


# ============================================================================
# Token Schema
# ============================================================================

class TokenResponse(BaseModel):
    """Legacy token response schema for backward compatibility."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse
