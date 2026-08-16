"""
Pydantic schemas for Evidence and Career Accomplishments.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class EvidenceTypeEnum(str, Enum):
    """Evidence type enumeration."""
    PROJECT = "project"
    POSITION = "position"
    ACHIEVEMENT = "achievement"
    CASE_STUDY = "case_study"
    PUBLICATION = "publication"
    CERTIFICATION = "certification"
    VOLUNTEER = "volunteer"
    OTHER = "other"


class EvidenceBase(BaseModel):
    """Base evidence schema."""
    title: str = Field(..., max_length=255, description="Evidence title")
    description: Optional[str] = Field(None, description="Detailed description")
    evidence_type: EvidenceTypeEnum = Field(..., description="Type of evidence")
    category: Optional[str] = Field(None, max_length=100, description="Category")
    organization: Optional[str] = Field(None, max_length=255, description="Organization name")
    position_title: Optional[str] = Field(None, max_length=255, description="Position title")
    outcome: Optional[str] = Field(None, description="Outcome or achievement")
    impact: Optional[str] = Field(None, description="Impact of the work")
    situation: Optional[str] = Field(None, description="STAR: Situation")
    task: Optional[str] = Field(None, description="STAR: Task")
    action: Optional[str] = Field(None, description="STAR: Action")
    result: Optional[str] = Field(None, description="STAR: Result")
    skills_demonstrated: Optional[str] = Field(None, description="Skills demonstrated")
    project_url: Optional[str] = Field(None, max_length=500, description="Project URL")
    is_public: bool = Field(default=False, description="Public visibility")
    is_featured: bool = Field(default=False, description="Featured in profile")


class EvidenceCreate(EvidenceBase):
    """Schema for creating evidence."""
    pass


class EvidenceUpdate(BaseModel):
    """Schema for updating evidence."""
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    outcome: Optional[str] = None
    impact: Optional[str] = None
    is_public: Optional[bool] = None
    is_featured: Optional[bool] = None


class EvidenceResponse(EvidenceBase):
    """Evidence response schema."""
    id: int
    user_id: int
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_current: bool = False
    is_verified: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EvidenceListResponse(BaseModel):
    """Evidence list response with pagination."""
    total: int
    items: list[EvidenceResponse]
    skip: int
    limit: int
