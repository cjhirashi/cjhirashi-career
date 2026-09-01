"""
Model stubs for IA service.

These are minimal models for type hints and testing.
Real models live in the monolith and are accessed via orchestrator_client.
"""

from datetime import datetime
from sqlalchemy import Column, DateTime, String, Integer, Float, Boolean
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class AgentSystemUsageLog(Base):
    """Stub for usage logging."""
    __tablename__ = "agent_system_usage_logs"

    id = Column(String, primary_key=True)
    user_id = Column(String)
    model_id = Column(String)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    cache_read_tokens = Column(Integer, default=0)
    cache_write_tokens = Column(Integer, default=0)
    estimated_cost_usd = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)


class AgentSystemTask(Base):
    """Stub for task execution."""
    __tablename__ = "agent_system_tasks"

    id = Column(String, primary_key=True)
    user_id = Column(String)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)


class User(Base):
    """Stub for user."""
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String)


class LinkedInConnection(Base):
    """Stub for LinkedIn."""
    __tablename__ = "linkedin_connections"

    id = Column(String, primary_key=True)


class LinkedInPost(Base):
    """Stub for LinkedIn posts."""
    __tablename__ = "linkedin_posts"

    id = Column(String, primary_key=True)
    status = Column(String, default="draft")


class LinkedInPostStatus:
    """Stub for post status."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    POSTED = "posted"


class PdfOutputTemplate(Base):
    """Stub for PDF templates."""
    __tablename__ = "pdf_output_templates"

    id = Column(String, primary_key=True)


class PdfTemplateStyle(Base):
    """Stub for PDF styles."""
    __tablename__ = "pdf_template_styles"

    id = Column(String, primary_key=True)
    slug = Column(String)
    title = Column(String)
    description = Column(String)
    css_content = Column(String)
    style_guide = Column(String)
    is_active = Column(Boolean, default=True)


__all__ = [
    "Base",
    "AgentSystemUsageLog",
    "AgentSystemTask",
    "User",
    "LinkedInConnection",
    "LinkedInPost",
    "LinkedInPostStatus",
    "PdfOutputTemplate",
    "PdfTemplateStyle",
]
