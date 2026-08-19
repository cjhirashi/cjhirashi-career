"""
Public, unauthenticated read-only API for the portfolio portal
(portal_publico, port 8003) - "Portal Público (Lectura): SOLO lectura de
proyectos, blog, about, contacto" per the project's architecture. Every
route here is scoped to the single portfolio owner (settings.PUBLIC_PORTAL_USER_ID)
and exposes nothing besides the content that's meant to be public - no
career-pipeline, application-tracking, or LinkedIn-connection data lives
under this router.
"""
import re
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from config import settings

from models.identity import Identity
from models.identity_reflection import IdentityReflection
from models.work_history import WorkHistory
from models.competencies import Competency
from models.certification import Certification
from models.project import Project
from models.publication import Publication
from models.linkedin_profile import LinkedInProfile
from models.github_profile import GitHubProfile
from models.portal_home import PortalHome
from models.portal_about import PortalAbout
from models.portal_contact import PortalContact

from schemas.public import (
    PublicHomeResponse, PublicProjectCard, PublicPublicationCard,
    PublicAboutResponse, PublicIkigaiReflection, PublicWorkHistoryEntry,
    PublicCompetency, PublicCertification,
    PublicContactResponse,
    PublicProjectDetail,
    PublicBlogPost,
)

router = APIRouter(prefix="/public", tags=["Public Portal"])

USER_ID = settings.PUBLIC_PORTAL_USER_ID


def _parse_lines(text: Optional[str]) -> List[str]:
    """Splits a "one item per line" Markdown-list field (see careerResources.ts's
    `textarea` convention) into a clean list, stripping "- "/"* " bullets."""
    if not text:
        return []
    lines = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        line = re.sub(r"^[-*]\s+", "", line)
        if line:
            lines.append(line)
    return lines


@router.get("/home", response_model=PublicHomeResponse)
async def get_home(db: AsyncSession = Depends(get_db)):
    home = (await db.execute(select(PortalHome).where(PortalHome.user_id == USER_ID))).scalar_one_or_none()
    # Falls back to Identity's tagline/bio when portal_home hasn't been
    # filled in yet, so Home isn't blank before that table has content.
    identity = (await db.execute(select(Identity).where(Identity.user_id == USER_ID))).scalar_one_or_none()

    projects = (
        await db.execute(select(Project).where(Project.user_id == USER_ID, Project.is_featured.is_(True)))
    ).scalars().all()

    publications = (
        await db.execute(
            select(Publication).where(
                Publication.user_id == USER_ID,
                Publication.featured_on_home.is_(True),
                Publication.status == "published",
            )
        )
    ).scalars().all()

    return PublicHomeResponse(
        hero_title=(home.hero_title if home else None) or (identity.professional_tagline if identity else None),
        hero_subtitle=home.hero_subtitle if home else None,
        hero_intro=(home.hero_intro if home else None) or (identity.bio_summary if identity else None),
        featured_projects=[
            PublicProjectCard(
                id=p.id, title=p.title, category=p.category, card_summary=p.card_summary,
                tech_stack=_parse_lines(p.tech_stack), github_url=p.github_url, demo_url=p.demo_url,
            )
            for p in projects
        ],
        featured_publications=[
            PublicPublicationCard(
                id=pub.id, title=pub.title, slug=pub.slug, excerpt=pub.excerpt, platform=pub.platform,
                published_at=pub.published_at, reading_minutes=pub.reading_minutes,
                tags=_parse_lines(pub.tags),
            )
            for pub in publications
        ],
    )


@router.get("/about", response_model=PublicAboutResponse)
async def get_about(db: AsyncSession = Depends(get_db)):
    identity = (await db.execute(select(Identity).where(Identity.user_id == USER_ID))).scalar_one_or_none()
    about = (await db.execute(select(PortalAbout).where(PortalAbout.user_id == USER_ID))).scalar_one_or_none()
    reflections = (
        await db.execute(select(IdentityReflection).where(IdentityReflection.user_id == USER_ID))
    ).scalars().all()
    history = (
        await db.execute(
            select(WorkHistory).where(WorkHistory.user_id == USER_ID).order_by(WorkHistory.start_date.desc())
        )
    ).scalars().all()
    competencies = (await db.execute(select(Competency).where(Competency.user_id == USER_ID))).scalars().all()
    certifications = (
        await db.execute(select(Certification).where(Certification.user_id == USER_ID))
    ).scalars().all()

    return PublicAboutResponse(
        professional_tagline=identity.professional_tagline if identity else None,
        bio_summary=identity.bio_summary if identity else None,
        unique_value_proposition=identity.unique_value_proposition if identity else None,
        photo_url=about.photo_url if about else None,
        values=_parse_lines(about.values if about else None),
        interests_hobbies=_parse_lines(about.interests_hobbies if about else None),
        personal_quote=about.personal_quote if about else None,
        ikigai=[PublicIkigaiReflection(dimension=r.dimension, content=r.content) for r in reflections],
        work_history=[
            PublicWorkHistoryEntry(
                company=w.company, role_title=w.role_title, start_date=w.start_date, end_date=w.end_date,
                description=w.description, achievements=w.achievements,
            )
            for w in history
        ],
        competencies=[
            PublicCompetency(
                name=c.name, type=c.type, category=c.category, level=c.level, is_highlighted=c.is_highlighted,
            )
            for c in competencies
        ],
        certifications=[
            PublicCertification(name=c.name, institution=c.institution, year=c.year) for c in certifications
        ],
    )


@router.get("/contact", response_model=PublicContactResponse)
async def get_contact(db: AsyncSession = Depends(get_db)):
    contact = (
        await db.execute(select(PortalContact).where(PortalContact.user_id == USER_ID))
    ).scalar_one_or_none()
    linkedin = (
        await db.execute(select(LinkedInProfile).where(LinkedInProfile.user_id == USER_ID))
    ).scalar_one_or_none()
    github = (
        await db.execute(select(GitHubProfile).where(GitHubProfile.user_id == USER_ID))
    ).scalar_one_or_none()

    return PublicContactResponse(
        contact_email=contact.contact_email if contact else None,
        location=contact.location if contact else None,
        availability_status=contact.availability_status if contact else None,
        preferred_contact_method=contact.preferred_contact_method if contact else None,
        footer_links=contact.footer_links if contact and contact.footer_links else [],
        linkedin_url=linkedin.profile_url if linkedin else None,
        github_url=github.profile_url if github else None,
    )


@router.get("/projects", response_model=List[PublicProjectDetail])
async def list_projects(db: AsyncSession = Depends(get_db)):
    projects = (
        await db.execute(
            select(Project).where(Project.user_id == USER_ID).order_by(Project.year.desc().nullslast())
        )
    ).scalars().all()
    return [
        PublicProjectDetail(
            id=p.id, title=p.title, category=p.category, industry=p.industry, year=p.year,
            card_summary=p.card_summary, detailed_summary=p.detailed_summary, problem=p.problem,
            solution=p.solution, architecture=p.architecture, tech_stack=_parse_lines(p.tech_stack),
            metrics=p.metrics, approach_steps=p.approach_steps, results=p.results,
            github_url=p.github_url, demo_url=p.demo_url, status=p.status, is_featured=bool(p.is_featured),
        )
        for p in projects
    ]


@router.get("/projects/{project_id}", response_model=PublicProjectDetail)
async def get_project(project_id: int, db: AsyncSession = Depends(get_db)):
    project = (
        await db.execute(select(Project).where(Project.user_id == USER_ID, Project.id == project_id))
    ).scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return PublicProjectDetail(
        id=project.id, title=project.title, category=project.category, industry=project.industry,
        year=project.year, card_summary=project.card_summary, detailed_summary=project.detailed_summary,
        problem=project.problem, solution=project.solution, architecture=project.architecture,
        tech_stack=_parse_lines(project.tech_stack), metrics=project.metrics,
        approach_steps=project.approach_steps, results=project.results,
        github_url=project.github_url, demo_url=project.demo_url, status=project.status,
        is_featured=bool(project.is_featured),
    )


@router.get("/blog", response_model=List[PublicBlogPost])
async def list_blog_posts(limit: int = Query(default=50, ge=1, le=100), db: AsyncSession = Depends(get_db)):
    posts = (
        await db.execute(
            select(Publication)
            .where(Publication.user_id == USER_ID, Publication.status == "published")
            .order_by(Publication.published_at.desc().nullslast())
            .limit(limit)
        )
    ).scalars().all()
    return [
        PublicBlogPost(
            id=post.id, title=post.title, slug=post.slug, excerpt=post.excerpt,
            body_content=post.body_content, content_type=post.content_type,
            tags=_parse_lines(post.tags), platform=post.platform, publication_url=post.publication_url,
            published_at=post.published_at, reading_minutes=post.reading_minutes,
        )
        for post in posts
    ]


@router.get("/blog/{slug}", response_model=PublicBlogPost)
async def get_blog_post(slug: str, db: AsyncSession = Depends(get_db)):
    post = (
        await db.execute(
            select(Publication).where(
                Publication.user_id == USER_ID, Publication.slug == slug, Publication.status == "published"
            )
        )
    ).scalar_one_or_none()
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return PublicBlogPost(
        id=post.id, title=post.title, slug=post.slug, excerpt=post.excerpt,
        body_content=post.body_content, content_type=post.content_type,
        tags=_parse_lines(post.tags), platform=post.platform, publication_url=post.publication_url,
        published_at=post.published_at, reading_minutes=post.reading_minutes,
    )
