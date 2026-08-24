"""
Pydantic schemas - Career domain (v2), Dominio 3: Presencia Digital.

Covers: publications, linkedin_profile, github_profile, portal_home,
portal_about, portal_contact.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Any, Literal
from datetime import datetime


# ============================================================================
# Publication
# ============================================================================

PublicationStatusLiteral = Literal["draft", "scheduled", "published"]


class PublicationBase(BaseModel):
    title: str = Field(..., max_length=255)
    slug: Optional[str] = Field(None, max_length=255)
    excerpt: Optional[str] = Field(None, max_length=500)
    body_content: Optional[str] = None
    content_type: Optional[str] = Field(None, max_length=50)
    tags: Optional[str] = None
    image_url: Optional[str] = Field(None, max_length=1024)
    platform: Optional[str] = Field(None, max_length=100)
    publication_url: Optional[str] = Field(None, max_length=500)
    published_at: Optional[datetime] = None
    views: Optional[int] = None
    likes_reactions: Optional[int] = None
    comments: Optional[int] = None
    shares: Optional[int] = None
    status: PublicationStatusLiteral = "draft"
    reading_minutes: Optional[int] = None
    featured_on_home: bool = False
    related_project_id: Optional[str] = None
    notes: Optional[str] = None


class PublicationCreate(PublicationBase):
    pass
    notes: Optional[str] = None


class PublicationUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    slug: Optional[str] = None
    excerpt: Optional[str] = None
    body_content: Optional[str] = None
    content_type: Optional[str] = None
    tags: Optional[str] = None
    image_url: Optional[str] = None
    platform: Optional[str] = None
    publication_url: Optional[str] = None
    published_at: Optional[datetime] = None
    views: Optional[int] = None
    likes_reactions: Optional[int] = None
    comments: Optional[int] = None
    shares: Optional[int] = None
    status: Optional[PublicationStatusLiteral] = None
    reading_minutes: Optional[int] = None
    featured_on_home: Optional[bool] = None
    related_project_id: Optional[str] = None
    notes: Optional[str] = None


class PublicationResponse(PublicationBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    notes: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================================
# LinkedInProfile (singleton)
# ============================================================================

class LinkedInProfileBase(BaseModel):
    headline: Optional[str] = Field(None, max_length=255)
    about: Optional[str] = None
    profile_url: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = Field(None, max_length=255)
    experience: Optional[List[Any]] = None
    education: Optional[List[Any]] = None
    featured_skills: Optional[str] = None
    featured_certifications: Optional[str] = None
    languages: Optional[str] = None
    notes: Optional[str] = None


class LinkedInProfileCreate(LinkedInProfileBase):
    pass
    notes: Optional[str] = None


class LinkedInProfileUpdate(LinkedInProfileBase):
    pass
    notes: Optional[str] = None


class LinkedInProfileResponse(LinkedInProfileBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    notes: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================================
# GitHubProfile (singleton)
# ============================================================================

class GitHubProfileBase(BaseModel):
    headline: Optional[str] = Field(None, max_length=255)
    bio: Optional[str] = None
    readme_markdown: Optional[str] = None
    profile_url: Optional[str] = Field(None, max_length=500)
    username: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None


class GitHubProfileCreate(GitHubProfileBase):
    pass
    notes: Optional[str] = None


class GitHubProfileUpdate(GitHubProfileBase):
    pass
    notes: Optional[str] = None


class GitHubProfileResponse(GitHubProfileBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    notes: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================================
# PortalHome (singleton)
# ============================================================================

class PortalHomeBase(BaseModel):
    hero_photo_url: Optional[str] = Field(None, max_length=1024)
    hero_title: Optional[str] = Field(None, max_length=255)
    hero_subtitle: Optional[str] = Field(None, max_length=500)
    hero_intro: Optional[str] = None
    cta1_label: Optional[str] = Field(None, max_length=100)
    cta1_url: Optional[str] = Field(None, max_length=1024)
    cta2_label: Optional[str] = Field(None, max_length=100)
    cta2_url: Optional[str] = Field(None, max_length=1024)
    stat1_label: Optional[str] = Field(None, max_length=100)
    stat1_value: Optional[str] = Field(None, max_length=50)
    stat2_label: Optional[str] = Field(None, max_length=100)
    stat2_value: Optional[str] = Field(None, max_length=50)
    stat3_label: Optional[str] = Field(None, max_length=100)
    stat3_value: Optional[str] = Field(None, max_length=50)
    stat4_label: Optional[str] = Field(None, max_length=100)
    stat4_value: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None


class PortalHomeCreate(PortalHomeBase):
    pass
    notes: Optional[str] = None


class PortalHomeUpdate(PortalHomeBase):
    pass
    notes: Optional[str] = None


class PortalHomeResponse(PortalHomeBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    notes: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================================
# PortalAbout (singleton)
# ============================================================================

class PortalAboutBase(BaseModel):
    photo_url: Optional[str] = Field(None, max_length=1024)
    name: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None


class PortalAboutCreate(PortalAboutBase):
    pass
    notes: Optional[str] = None


class PortalAboutUpdate(PortalAboutBase):
    pass
    notes: Optional[str] = None


class PortalAboutResponse(PortalAboutBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    notes: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================================
# PortalContact (singleton)
# ============================================================================

class PortalContactBase(BaseModel):
    contact_email: Optional[str] = Field(None, max_length=255)
    whatsapp: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, max_length=255)
    availability_status: Optional[str] = Field(None, max_length=50)
    preferred_contact_method: Optional[str] = Field(None, max_length=100)
    footer_links: Optional[List[Any]] = None
    notes: Optional[str] = None


class PortalContactCreate(PortalContactBase):
    pass
    notes: Optional[str] = None


class PortalContactUpdate(PortalContactBase):
    pass
    notes: Optional[str] = None


class PortalContactResponse(PortalContactBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    notes: Optional[str] = None

    class Config:
        from_attributes = True
