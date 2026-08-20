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
# Shared project/publication shapes
# ============================================================================

class PublicProjectCard(BaseModel):
    id: int
    title: str
    category: Optional[str] = None
    industry: Optional[str] = None
    year: Optional[int] = None
    card_summary: Optional[str] = None
    tech_stack: List[str] = []
    metrics: Optional[Any] = None
    image_url: Optional[str] = None
    github_url: Optional[str] = None
    demo_url: Optional[str] = None


class PublicProjectDetail(PublicProjectCard):
    detailed_summary: Optional[str] = None
    problem: Optional[str] = None
    solution: Optional[str] = None
    architecture: Optional[str] = None
    approach_steps: Optional[str] = None
    results: Optional[Any] = None
    status: Optional[str] = None
    is_featured: bool = False
    is_anchor: bool = False


class PublicPublicationCard(BaseModel):
    id: int
    title: str
    slug: Optional[str] = None
    excerpt: Optional[str] = None
    image_url: Optional[str] = None
    content_type: Optional[str] = None
    platform: Optional[str] = None
    published_at: Optional[datetime] = None
    reading_minutes: Optional[int] = None
    tags: List[str] = []


class PublicBlogPost(PublicPublicationCard):
    body_content: Optional[str] = None
    publication_url: Optional[str] = None


# ============================================================================
# Home
# ============================================================================

class PublicStat(BaseModel):
    label: str
    value: str


class PublicHeroCta(BaseModel):
    label: str
    url: str


class PublicHomeResponse(BaseModel):
    hero_photo_url: Optional[str] = None
    hero_title: Optional[str] = None
    hero_subtitle: Optional[str] = None
    hero_intro: Optional[str] = None
    hero_ctas: List[PublicHeroCta] = []
    stats: List[PublicStat] = []
    # The single is_anchor project, rendered as a full case-study block -
    # None if no project is currently marked as the anchor.
    anchor_project: Optional[PublicProjectDetail] = None
    featured_projects: List[PublicProjectCard] = []
    featured_publications: List[PublicPublicationCard] = []


# ============================================================================
# About
# ============================================================================

class PublicWorkHistoryEntry(BaseModel):
    company: str
    role_title: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: Optional[str] = None
    narrative: Optional[str] = None
    achievements: Optional[str] = None
    key_metrics: Optional[Any] = None


class PublicSkillGroup(BaseModel):
    category: str
    skills: List[str]


class PublicCertification(BaseModel):
    name: str
    institution: Optional[str] = None
    year: Optional[int] = None


class PublicAboutResponse(BaseModel):
    professional_tagline: Optional[str] = None
    bio_summary: Optional[str] = None
    unique_value_proposition: Optional[str] = None
    photo_url: Optional[str] = None
    work_history: List[PublicWorkHistoryEntry] = []
    skill_groups: List[PublicSkillGroup] = []
    certifications: List[PublicCertification] = []


# ============================================================================
# Contact
# ============================================================================

class PublicContactResponse(BaseModel):
    contact_email: Optional[str] = None
    whatsapp: Optional[str] = None
    location: Optional[str] = None
    availability_status: Optional[str] = None
    preferred_contact_method: Optional[str] = None
    footer_links: List[Any] = []
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
