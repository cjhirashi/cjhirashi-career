"""
Pydantic schemas - Career domain (v2), Dominio 3: Presencia Digital.

Covers: digital_platforms, content_pieces, publications.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Any, Literal
from datetime import datetime


# ============================================================================
# DigitalPlatform
# ============================================================================

PlatformNameLiteral = Literal[
    "linkedin", "github", "kaggle", "portfolio_web", "medium", "twitter", "other"
]


class DigitalPlatformBase(BaseModel):
    platform_name: Optional[PlatformNameLiteral] = None
    profile_url: Optional[str] = Field(None, max_length=500)
    profile_status: Optional[str] = Field(None, max_length=30)
    platform_strategy: Optional[str] = None
    followers_count: Optional[int] = None
    is_active_in_search: bool = True


class DigitalPlatformCreate(DigitalPlatformBase):
    pass


class DigitalPlatformUpdate(BaseModel):
    platform_name: Optional[PlatformNameLiteral] = None
    profile_url: Optional[str] = None
    profile_status: Optional[str] = None
    platform_strategy: Optional[str] = None
    followers_count: Optional[int] = None
    is_active_in_search: Optional[bool] = None


class DigitalPlatformResponse(DigitalPlatformBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# ContentPiece
# ============================================================================

ContentStatusLiteral = Literal["draft", "scheduled", "published"]


class ContentPieceBase(BaseModel):
    title: str = Field(..., max_length=255)
    slug: Optional[str] = Field(None, max_length=255)
    excerpt: Optional[str] = Field(None, max_length=500)
    body_content: Optional[str] = None
    content_type: Optional[str] = Field(None, max_length=50)
    thematic_pillar: Optional[str] = Field(None, max_length=100)
    tags: Optional[str] = None
    status: ContentStatusLiteral = "draft"
    reading_minutes: Optional[int] = None
    featured_on_home: bool = False
    scheduled_publish_at: Optional[datetime] = None
    related_project_id: Optional[int] = None
    related_achievement_id: Optional[int] = None
    related_competency_id: Optional[int] = None


class ContentPieceCreate(ContentPieceBase):
    pass


class ContentPieceUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    slug: Optional[str] = None
    excerpt: Optional[str] = None
    body_content: Optional[str] = None
    content_type: Optional[str] = None
    thematic_pillar: Optional[str] = None
    tags: Optional[str] = None
    status: Optional[ContentStatusLiteral] = None
    reading_minutes: Optional[int] = None
    featured_on_home: Optional[bool] = None
    scheduled_publish_at: Optional[datetime] = None
    related_project_id: Optional[int] = None
    related_achievement_id: Optional[int] = None
    related_competency_id: Optional[int] = None


class ContentPieceResponse(ContentPieceBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Publication
# ============================================================================

class PublicationBase(BaseModel):
    content_piece_id: int
    platform_id: int
    published_title: Optional[str] = Field(None, max_length=255)
    publication_url: Optional[str] = Field(None, max_length=500)
    published_at: Optional[datetime] = None
    full_content: Optional[str] = None
    char_length: Optional[int] = None
    hashtags_used: Optional[str] = None
    views: Optional[int] = None
    likes_reactions: Optional[int] = None
    comments: Optional[int] = None
    shares: Optional[int] = None
    content_status: ContentStatusLiteral = "draft"


class PublicationCreate(PublicationBase):
    pass


class PublicationUpdate(BaseModel):
    published_title: Optional[str] = None
    publication_url: Optional[str] = None
    published_at: Optional[datetime] = None
    full_content: Optional[str] = None
    char_length: Optional[int] = None
    hashtags_used: Optional[str] = None
    views: Optional[int] = None
    likes_reactions: Optional[int] = None
    comments: Optional[int] = None
    shares: Optional[int] = None
    content_status: Optional[ContentStatusLiteral] = None


class PublicationResponse(PublicationBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
