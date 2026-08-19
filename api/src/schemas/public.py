"""
Pydantic schemas for the unauthenticated /public/* portal-read API
(routes/public.py). Text columns that the admin edits as "one item per
line" Markdown lists (tech_stack, tags, etc.) are exposed here already
split into `List[str]`, so the portal never has to know that convention.
"""
from datetime import date, datetime
from typing import Any, List, Optional

from pydantic import BaseModel


# ============================================================================
# Home
# ============================================================================

class PublicProjectCard(BaseModel):
    id: int
    title: str
    category: Optional[str] = None
    card_summary: Optional[str] = None
    tech_stack: List[str] = []
    github_url: Optional[str] = None
    demo_url: Optional[str] = None


class PublicPublicationCard(BaseModel):
    id: int
    title: str
    slug: Optional[str] = None
    excerpt: Optional[str] = None
    platform: Optional[str] = None
    published_at: Optional[datetime] = None
    reading_minutes: Optional[int] = None
    tags: List[str] = []


class PublicHomeResponse(BaseModel):
    hero_title: Optional[str] = None
    hero_subtitle: Optional[str] = None
    hero_intro: Optional[str] = None
    featured_projects: List[PublicProjectCard] = []
    featured_publications: List[PublicPublicationCard] = []


# ============================================================================
# About
# ============================================================================

class PublicIkigaiReflection(BaseModel):
    dimension: str
    content: Optional[str] = None


class PublicWorkHistoryEntry(BaseModel):
    company: str
    role_title: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: Optional[str] = None
    achievements: Optional[str] = None


class PublicCompetency(BaseModel):
    name: str
    type: str
    category: Optional[str] = None
    level: Optional[str] = None
    is_highlighted: Optional[bool] = None


class PublicCertification(BaseModel):
    name: str
    institution: Optional[str] = None
    year: Optional[int] = None


class PublicAboutResponse(BaseModel):
    professional_tagline: Optional[str] = None
    bio_summary: Optional[str] = None
    unique_value_proposition: Optional[str] = None
    photo_url: Optional[str] = None
    values: List[str] = []
    interests_hobbies: List[str] = []
    personal_quote: Optional[str] = None
    ikigai: List[PublicIkigaiReflection] = []
    work_history: List[PublicWorkHistoryEntry] = []
    competencies: List[PublicCompetency] = []
    certifications: List[PublicCertification] = []


# ============================================================================
# Contact
# ============================================================================

class PublicContactResponse(BaseModel):
    contact_email: Optional[str] = None
    location: Optional[str] = None
    availability_status: Optional[str] = None
    preferred_contact_method: Optional[str] = None
    footer_links: List[Any] = []
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None


# ============================================================================
# Projects
# ============================================================================

class PublicProjectDetail(BaseModel):
    id: int
    title: str
    category: Optional[str] = None
    industry: Optional[str] = None
    year: Optional[int] = None
    card_summary: Optional[str] = None
    detailed_summary: Optional[str] = None
    problem: Optional[str] = None
    solution: Optional[str] = None
    architecture: Optional[str] = None
    tech_stack: List[str] = []
    metrics: Optional[Any] = None
    approach_steps: Optional[str] = None
    results: Optional[Any] = None
    github_url: Optional[str] = None
    demo_url: Optional[str] = None
    status: Optional[str] = None
    is_featured: bool = False


# ============================================================================
# Blog
# ============================================================================

class PublicBlogPost(BaseModel):
    id: int
    title: str
    slug: Optional[str] = None
    excerpt: Optional[str] = None
    body_content: Optional[str] = None
    content_type: Optional[str] = None
    tags: List[str] = []
    platform: Optional[str] = None
    publication_url: Optional[str] = None
    published_at: Optional[datetime] = None
    reading_minutes: Optional[int] = None
