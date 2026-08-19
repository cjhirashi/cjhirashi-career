"""
Pydantic schemas for the LinkedIn integration (connection status, posting).
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class LinkedInStatusResponse(BaseModel):
    connected: bool
    member_name: Optional[str] = None
    member_email: Optional[str] = None
    profile_picture_url: Optional[str] = None
    expires_at: Optional[datetime] = None


class LinkedInConnectResponse(BaseModel):
    authorize_url: str


class LinkedInPostCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=3000)


class LinkedInPostResponse(BaseModel):
    id: int
    text: str
    linkedin_post_urn: Optional[str] = None
    published_at: datetime

    class Config:
        from_attributes = True
