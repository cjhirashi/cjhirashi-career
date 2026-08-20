"""
Project Model - Portfolio projects (public-facing and internal detail).
Career domain (v2) - Identity.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from database import Base


class Project(Base):
    """A project shown on the CV / portal, with technical detail and results."""

    __tablename__ = "projects"
    __table_args__ = (CheckConstraint("status IN ('active', 'in_development', 'archived')"),)

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    title = Column(String(255), nullable=False)
    category = Column(String(50), nullable=True)
    industry = Column(String(100), nullable=True)
    year = Column(Integer, nullable=True)
    card_summary = Column(String(500), nullable=True)
    detailed_summary = Column(Text, nullable=True)
    problem = Column(Text, nullable=True)
    solution = Column(Text, nullable=True)
    architecture = Column(Text, nullable=True)
    tech_stack = Column(Text, nullable=True)
    # Up to 4 metrics (name + value) - fixed slots instead of a JSON blob so
    # the admin form is 2 plain fields per metric, not hand-written JSON.
    # None are required; an unused slot is just left blank.
    metric1_label = Column(String(100), nullable=True)
    metric1_value = Column(String(500), nullable=True)
    metric2_label = Column(String(100), nullable=True)
    metric2_value = Column(String(500), nullable=True)
    metric3_label = Column(String(100), nullable=True)
    metric3_value = Column(String(500), nullable=True)
    metric4_label = Column(String(100), nullable=True)
    metric4_value = Column(String(500), nullable=True)
    approach_steps = Column(Text, nullable=True)
    results = Column(JSONB, nullable=True)
    github_url = Column(String(500), nullable=True)
    demo_url = Column(String(500), nullable=True)
    repo_structure = Column(Text, nullable=True)
    evidence_sources = Column(Text, nullable=True)
    releases = Column(JSONB, nullable=True)
    status = Column(String(30), default="active", nullable=True, index=True)
    is_featured = Column(Boolean, default=False, nullable=True, index=True)
    # The single flagship project the portal's Home page renders as a full
    # case-study block (problem/architecture/result narrative), separate
    # from is_featured (which drives the plain project-card grid). Not
    # DB-enforced to be unique - the portal just uses the first match.
    is_anchor = Column(Boolean, default=False, nullable=True, index=True)
    image_url = Column(String(1024), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<Project(id={self.id}, title='{self.title}')>"
