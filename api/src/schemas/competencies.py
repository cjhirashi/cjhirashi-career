"""
Pydantic schemas for Competencies.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class CompetencyTypeEnum(str, Enum):
    """Competency type enumeration."""
    TECHNICAL = "technical"
    TRANSFERABLE = "transferable"
    BUSINESS = "business"


class CompetencyLevelEnum(str, Enum):
    """Proficiency level enumeration."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class CompetencyBase(BaseModel):
    """Base competency schema."""
    name: str = Field(..., max_length=255, description="Skill name")
    description: Optional[str] = Field(None, description="Skill description")
    competency_type: CompetencyTypeEnum = Field(..., description="Type of competency")
    proficiency_level: CompetencyLevelEnum = Field(default=CompetencyLevelEnum.INTERMEDIATE, description="Proficiency level")
    proficiency_score: Optional[float] = Field(default=50.0, ge=0, le=100, description="Proficiency score 0-100")
    category: Optional[str] = Field(None, max_length=100, description="Category for organization")
    years_of_experience: Optional[float] = Field(None, description="Years of experience")
    certification_url: Optional[str] = Field(None, max_length=500, description="Certification URL")
    keywords: Optional[str] = Field(None, max_length=500, description="SEO keywords")
    is_featured: bool = Field(default=False, description="Featured in profile")
    notes: Optional[str] = None


class CompetencyCreate(CompetencyBase):
    """Schema for creating competency."""
    pass
    notes: Optional[str] = None


class CompetencyUpdate(BaseModel):
    """Schema for updating competency."""
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    proficiency_level: Optional[CompetencyLevelEnum] = None
    proficiency_score: Optional[float] = Field(None, ge=0, le=100)
    category: Optional[str] = None
    years_of_experience: Optional[float] = None
    is_featured: Optional[bool] = None
    notes: Optional[str] = None


class CompetencyResponse(CompetencyBase):
    """Competency response schema."""
    id: str
    user_id: str
    endorsement_count: int = 0
    is_verified: bool = False
    created_at: datetime
    updated_at: datetime
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class CompetencyListResponse(BaseModel):
    """Competency list response with pagination."""
    total: int
    items: list[CompetencyResponse]
    skip: int
    limit: int
    notes: Optional[str] = None
