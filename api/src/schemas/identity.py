"""
Pydantic schemas for Identity/Professional Profile.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class IdentityBase(BaseModel):
    """Base identity schema."""
    passion: Optional[str] = Field(None, description="What you love doing (passion)")
    mission: Optional[str] = Field(None, description="What you believe in (mission)")
    vocation: Optional[str] = Field(None, description="What you're good at (vocation)")
    profession: Optional[str] = Field(None, description="What the world needs (profession)")
    key_strengths: Optional[str] = Field(None, description="Top 3-5 unique strengths")
    unique_value_prop: Optional[str] = Field(None, description="What makes you different")
    professional_narrative: Optional[str] = Field(None, description="Your professional story")
    career_objective: Optional[str] = Field(None, description="Long-term career goal")
    value_proposition: Optional[str] = Field(None, description="Concise value statement for employers")
    elevator_pitch: Optional[str] = Field(None, max_length=500, description="30-second pitch")
    bio: Optional[str] = Field(None, description="Extended professional bio")
    about_me: Optional[str] = Field(None, description="About me section")
    keywords: Optional[str] = Field(None, description="Comma-separated professional keywords")
    tagline: Optional[str] = Field(None, max_length=255, description="Professional tagline")


class IdentityCreate(IdentityBase):
    """Schema for creating identity."""
    pass


class IdentityUpdate(IdentityBase):
    """Schema for updating identity."""
    pass


class IdentityResponse(IdentityBase):
    """Identity response schema."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
