"""Pydantic models for PDF Generator requests and responses."""

from typing import List, Optional
from pydantic import BaseModel, EmailStr, HttpUrl, Field


class CompetencyRequest(BaseModel):
    """Competency model."""

    category: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    level: str = Field(..., min_length=1, max_length=50)


class ExperienceRequest(BaseModel):
    """Experience model."""

    position: str = Field(..., min_length=1, max_length=200)
    company: str = Field(..., min_length=1, max_length=200)
    start_date: str = Field(..., pattern=r"^\d{4}-\d{2}$")  # YYYY-MM format
    end_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}$|^present$")
    description: str = Field(..., min_length=10, max_length=1000)


class EducationRequest(BaseModel):
    """Education model."""

    degree: str = Field(..., min_length=1, max_length=200)
    school: str = Field(..., min_length=1, max_length=200)
    field: str = Field(..., min_length=1, max_length=200)
    year: str = Field(..., pattern=r"^\d{4}$")


class ProjectRequest(BaseModel):
    """Project model."""

    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=10, max_length=1000)
    technologies: List[str] = Field(..., min_items=1, max_items=20)
    link: Optional[HttpUrl] = None


class CVRequest(BaseModel):
    """Request model for CV generation."""

    name: str = Field(..., min_length=1, max_length=200)
    email: EmailStr
    phone: str = Field(..., min_length=5, max_length=20)
    location: str = Field(..., min_length=1, max_length=200)
    ikigai: str = Field(..., min_length=10, max_length=500)
    about: str = Field(..., min_length=20, max_length=2000)
    competencies: List[CompetencyRequest] = Field(..., min_items=1, max_items=50)
    experience: List[ExperienceRequest] = Field(..., min_items=0, max_items=50)
    education: List[EducationRequest] = Field(..., min_items=0, max_items=20)
    projects: List[ProjectRequest] = Field(default_factory=list, max_items=50)


class CoverLetterRequest(BaseModel):
    """Request model for Cover Letter generation."""

    name: str = Field(..., min_length=1, max_length=200)
    email: EmailStr
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")  # YYYY-MM-DD format
    company_name: str = Field(..., min_length=1, max_length=200)
    company_address: str = Field(..., min_length=1, max_length=500)
    recipient_name: str = Field(..., min_length=1, max_length=200)
    position: str = Field(..., min_length=1, max_length=200)
    body: str = Field(..., min_length=50, max_length=5000)
    closing_statement: str = Field(..., min_length=10, max_length=500)
    signature: str = Field(..., min_length=1, max_length=200)

    class Config:
        """Pydantic config."""

        populate_by_name = True


class PDFResponse(BaseModel):
    """Response model for PDF generation."""

    filename: str
    size_bytes: int
    generated_at: str
