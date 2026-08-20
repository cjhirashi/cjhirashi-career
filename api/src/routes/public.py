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
from collections import OrderedDict
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from config import settings

from models.identity import Identity
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
    PublicHomeResponse, PublicProjectCard, PublicProjectDetail, PublicPublicationCard,
    PublicAboutResponse, PublicWorkHistoryEntry, PublicSkillGroup, PublicCertification,
    PublicContactResponse,
    PublicBlogPost, PublicHeroCta, PublicStat,
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


def _project_card(p: Project) -> PublicProjectCard:
    return PublicProjectCard(
        id=p.id, title=p.title, category=p.category, industry=p.industry, year=p.year,
        card_summary=p.card_summary, tech_stack=_parse_lines(p.tech_stack), metrics=p.metrics,
        image_url=p.image_url, github_url=p.github_url, demo_url=p.demo_url,
    )


def _project_detail(p: Project) -> PublicProjectDetail:
    return PublicProjectDetail(
        **_project_card(p).model_dump(),
        detailed_summary=p.detailed_summary, problem=p.problem, solution=p.solution,
        architecture=p.architecture, approach_steps=p.approach_steps, results=p.results,
        status=p.status, is_featured=bool(p.is_featured), is_anchor=bool(p.is_anchor),
    )


def _publication_card(pub: Publication) -> PublicPublicationCard:
    return PublicPublicationCard(
        id=pub.id, title=pub.title, slug=pub.slug, excerpt=pub.excerpt, image_url=pub.image_url,
        content_type=pub.content_type, platform=pub.platform, published_at=pub.published_at,
        reading_minutes=pub.reading_minutes, tags=_parse_lines(pub.tags),
    )


def _blog_post(pub: Publication) -> PublicBlogPost:
    return PublicBlogPost(
        **_publication_card(pub).model_dump(),
        body_content=pub.body_content, publication_url=pub.publication_url,
    )


def _hero_ctas(home: Optional[PortalHome]) -> List[PublicHeroCta]:
    if not home:
        return []
    slots = [(home.cta1_label, home.cta1_url), (home.cta2_label, home.cta2_url)]
    return [PublicHeroCta(label=label, url=url) for label, url in slots if label and url]


def _stats(home: Optional[PortalHome]) -> List[PublicStat]:
    if not home:
        return []
    slots = [
        (home.stat1_label, home.stat1_value), (home.stat2_label, home.stat2_value),
        (home.stat3_label, home.stat3_value), (home.stat4_label, home.stat4_value),
    ]
    return [PublicStat(label=label, value=value) for label, value in slots if label and value]


@router.get("/home", response_model=PublicHomeResponse)
async def get_home(db: AsyncSession = Depends(get_db)):
    # No fallback to Identity here on purpose: what's in the Portal · Home
    # admin form is exactly what the Home page shows, nothing borrowed
    # silently from another table - empty field means empty on the site.
    home = (await db.execute(select(PortalHome).where(PortalHome.user_id == USER_ID))).scalar_one_or_none()

    anchor = (
        await db.execute(select(Project).where(Project.user_id == USER_ID, Project.is_anchor.is_(True)))
    ).scalar_one_or_none()

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
        hero_photo_url=home.hero_photo_url if home else None,
        hero_title=home.hero_title if home else None,
        hero_subtitle=home.hero_subtitle if home else None,
        hero_intro=home.hero_intro if home else None,
        hero_ctas=_hero_ctas(home),
        stats=_stats(home),
        anchor_project=_project_detail(anchor) if anchor else None,
        featured_projects=[_project_card(p) for p in projects],
        featured_publications=[_publication_card(pub) for pub in publications],
    )


@router.get("/about", response_model=PublicAboutResponse)
async def get_about(db: AsyncSession = Depends(get_db)):
    identity = (await db.execute(select(Identity).where(Identity.user_id == USER_ID))).scalar_one_or_none()
    about = (await db.execute(select(PortalAbout).where(PortalAbout.user_id == USER_ID))).scalar_one_or_none()
    history = (
        await db.execute(
            select(WorkHistory).where(WorkHistory.user_id == USER_ID).order_by(WorkHistory.start_date.desc())
        )
    ).scalars().all()
    competencies = (await db.execute(select(Competency).where(Competency.user_id == USER_ID))).scalars().all()
    certifications = (
        await db.execute(select(Certification).where(Certification.user_id == USER_ID))
    ).scalars().all()

    # Group skills by category, same clustering as cjhirashi.com's "Stack"
    # section (e.g. "Data Science & ML", "Arquitectura & Sistemas Críticos") -
    # driven entirely by whatever `category` values are actually in the data.
    grouped: "OrderedDict[str, list[str]]" = OrderedDict()
    for c in competencies:
        key = c.category or "Otros"
        grouped.setdefault(key, []).append(c.name)

    return PublicAboutResponse(
        professional_tagline=identity.professional_tagline if identity else None,
        bio_summary=identity.bio_summary if identity else None,
        unique_value_proposition=identity.unique_value_proposition if identity else None,
        photo_url=about.photo_url if about else None,
        work_history=[
            PublicWorkHistoryEntry(
                company=w.company, role_title=w.role_title, start_date=w.start_date, end_date=w.end_date,
                description=w.description, narrative=w.narrative, achievements=w.achievements,
                key_metrics=w.key_metrics,
            )
            for w in history
        ],
        skill_groups=[PublicSkillGroup(category=category, skills=skills) for category, skills in grouped.items()],
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
        whatsapp=contact.whatsapp if contact else None,
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
    return [_project_detail(p) for p in projects]


@router.get("/projects/{project_id}", response_model=PublicProjectDetail)
async def get_project(project_id: int, db: AsyncSession = Depends(get_db)):
    project = (
        await db.execute(select(Project).where(Project.user_id == USER_ID, Project.id == project_id))
    ).scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return _project_detail(project)


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
    return [_blog_post(post) for post in posts]


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
    return _blog_post(post)
