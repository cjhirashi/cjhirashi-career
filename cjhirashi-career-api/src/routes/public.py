"""
Public, unauthenticated read-only API for the portfolio portal
(portal_publico, port 8003) - "Portal Público (Lectura): SOLO lectura de
proyectos, blog, about, contacto" per the project's architecture. Every
route here is scoped to the single portfolio owner (settings.PUBLIC_PORTAL_USER_ID)
and exposes nothing besides the content that's meant to be public - no
career-pipeline, application-tracking, or LinkedIn-connection data lives
under this router.
"""
# ============================================================================
# Imports
# ============================================================================
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
from models.achievement import Achievement
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
    PublicAboutResponse, PublicWorkHistoryEntry, PublicWorkAchievement, PublicSkillGroup, PublicCertification,
    PublicContactResponse,
    PublicBlogPost, PublicHeroCta, PublicStat, PublicAchievementDetail,
)

# ============================================================================
# Router principal y constantes
# ============================================================================
router = APIRouter(prefix="/public", tags=["Public Portal"])

USER_ID = settings.PUBLIC_PORTAL_USER_ID

# `Publication.platform` is free text (LinkedIn, Blog propio, Medium...) - the
# same article can have one row per platform it was cross-posted to (e.g. one
# "portfolio_web" row and one "linkedin" row sharing the same slug). Only the
# "portfolio_web" row is an actual page on this portal; the rest are
# cross-post records for other channels and must not be listed/linked here,
# or two rows sharing a slug make the detail lookup ambiguous.
PORTAL_BLOG_PLATFORM = "portfolio_web"


# ============================================================================
# Helpers y mappers de respuesta
# ============================================================================
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


async def _competency_names_by_id(db: AsyncSession) -> dict:
    """Id -> name for every competency of the (single) portal owner, loaded
    once per request so `_project_card`/`_project_detail` can resolve
    `Project.competency_ids` without a query per project."""
    result = await db.execute(select(Competency.id, Competency.name).where(Competency.user_id == USER_ID))
    return dict(result.all())


def _project_metrics(p: Project) -> List[PublicStat]:
    # A metric's name is optional (some are standalone achievement lines with
    # no natural label) - only the value decides whether a slot is shown.
    slots = [
        (p.metric1_label, p.metric1_value), (p.metric2_label, p.metric2_value),
        (p.metric3_label, p.metric3_value), (p.metric4_label, p.metric4_value),
    ]
    return [PublicStat(label=label or "", value=value) for label, value in slots if value]


def _project_tech_stack(p: Project, competency_names: dict) -> List[str]:
    return [competency_names[cid] for cid in (p.competency_ids or []) if cid in competency_names]


def _project_card(p: Project, competency_names: dict) -> PublicProjectCard:
    return PublicProjectCard(
        id=p.id, title=p.title, category=p.category, industry=p.industry, year=p.year,
        card_summary=p.card_summary, tech_stack=_project_tech_stack(p, competency_names),
        metrics=_project_metrics(p),
        image_url=p.image_url, github_url=p.github_url, demo_url=p.demo_url,
    )


def _project_detail(p: Project, competency_names: dict) -> PublicProjectDetail:
    return PublicProjectDetail(
        **_project_card(p, competency_names).model_dump(),
        detailed_summary=p.detailed_summary, problem=p.problem, solution=p.solution,
        architecture=p.architecture, approach_steps=p.approach_steps, results=p.results,
        status=p.status, is_featured=bool(p.is_featured),
    )


def _achievement_detail(a: Achievement) -> PublicAchievementDetail:
    return PublicAchievementDetail(
        id=a.id, title=a.title, challenge=a.challenge, solution=a.solution,
        executive_storytelling=a.executive_storytelling, impact_metrics=a.impact_metrics,
        documentation_urls=a.documentation_urls,
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


# ============================================================================
# Endpoint: página Home
# ============================================================================
@router.get("/home", response_model=PublicHomeResponse)
async def get_home(db: AsyncSession = Depends(get_db)):
    # No fallback to Identity here on purpose: what's in the Portal · Home
    # admin form is exactly what the Home page shows, nothing borrowed
    # silently from another table - empty field means empty on the site.
    home = (await db.execute(select(PortalHome).where(PortalHome.user_id == USER_ID))).scalar_one_or_none()

    # home is not unique in the DB; take the first match so a second
    # flagged achievement cannot 500 the whole Home page.
    home_achievement = (
        await db.execute(select(Achievement).where(Achievement.user_id == USER_ID, Achievement.home.is_(True)))
    ).scalars().first()

    # The Home is a highlight reel, not the full catalog - cap both sections
    # at 3 cards each (matches the reference cjhirashi.com layout) even if
    # more records end up marked as featured; the full sets still live on
    # /projects and /blog.
    projects = (
        await db.execute(
            select(Project)
            .where(Project.user_id == USER_ID, Project.is_featured.is_(True))
            .order_by(Project.year.desc().nullslast())
            .limit(3)
        )
    ).scalars().all()

    publications = (
        await db.execute(
            select(Publication)
            .where(
                Publication.user_id == USER_ID,
                Publication.featured_on_home.is_(True),
                Publication.status == "published",
                Publication.platform == PORTAL_BLOG_PLATFORM,
            )
            .order_by(Publication.published_at.desc().nullslast())
            .limit(3)
        )
    ).scalars().all()

    featured_competencies = (
        await db.execute(
            select(Competency)
            .where(Competency.user_id == USER_ID, Competency.featured_on_home.is_(True))
            .order_by(Competency.id)
        )
    ).scalars().all()
    # Distinct categories, first-seen order - a category can have several
    # featured competencies, it should still only produce one badge.
    skill_categories = list(dict.fromkeys(c.category for c in featured_competencies if c.category))
    competency_names = await _competency_names_by_id(db)

    return PublicHomeResponse(
        hero_photo_url=home.hero_photo_url if home else None,
        hero_title=home.hero_title if home else None,
        hero_subtitle=home.hero_subtitle if home else None,
        hero_intro=home.hero_intro if home else None,
        hero_ctas=_hero_ctas(home),
        stats=_stats(home),
        home_achievement=_achievement_detail(home_achievement) if home_achievement else None,
        featured_projects=[_project_card(p, competency_names) for p in projects],
        featured_publications=[_publication_card(pub) for pub in publications],
        skill_categories=skill_categories,
    )


# ============================================================================
# Endpoint: página About
# ============================================================================
@router.get("/about", response_model=PublicAboutResponse)
async def get_about(db: AsyncSession = Depends(get_db)):
    identity = (await db.execute(select(Identity).where(Identity.user_id == USER_ID))).scalar_one_or_none()
    about = (await db.execute(select(PortalAbout).where(PortalAbout.user_id == USER_ID))).scalar_one_or_none()
    history = (
        await db.execute(
            select(WorkHistory).where(WorkHistory.user_id == USER_ID).order_by(WorkHistory.start_date.desc())
        )
    ).scalars().all()
    portal_achievements = (
        await db.execute(
            select(Achievement).where(
                Achievement.user_id == USER_ID,
                Achievement.visible_on_portal.is_(True),
                Achievement.work_history_id.is_not(None),
            )
        )
    ).scalars().all()
    achievements_by_work: dict[str, list] = {}
    for achievement in portal_achievements:
        achievements_by_work.setdefault(achievement.work_history_id, []).append(achievement)
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
        name=about.name if about else None,
        professional_tagline=identity.professional_tagline if identity else None,
        bio_summary=identity.bio_summary if identity else None,
        unique_value_proposition=identity.unique_value_proposition if identity else None,
        photo_url=about.photo_url if about else None,
        work_history=[
            PublicWorkHistoryEntry(
                company=w.company, role_title=w.role_title, start_date=w.start_date, end_date=w.end_date,
                description=w.description, key_metrics=w.key_metrics,
                achievements=[
                    PublicWorkAchievement(
                        id=a.id, title=a.title, executive_storytelling=a.executive_storytelling,
                    )
                    for a in achievements_by_work.get(w.id, [])
                ],
            )
            for w in history
        ],
        skill_groups=[PublicSkillGroup(category=category, skills=skills) for category, skills in grouped.items()],
        certifications=[
            PublicCertification(
                name=c.name, institution=c.institution, year=c.year, description=c.description,
            )
            for c in certifications
        ],
    )


# ============================================================================
# Endpoint: página Contact
# ============================================================================
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


# ============================================================================
# Endpoints: proyectos
# ============================================================================
@router.get("/projects", response_model=List[PublicProjectDetail])
async def list_projects(db: AsyncSession = Depends(get_db)):
    projects = (
        await db.execute(
            select(Project).where(Project.user_id == USER_ID).order_by(Project.year.desc().nullslast())
        )
    ).scalars().all()
    competency_names = await _competency_names_by_id(db)
    return [_project_detail(p, competency_names) for p in projects]


@router.get("/projects/{project_id}", response_model=PublicProjectDetail)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    project = (
        await db.execute(select(Project).where(Project.user_id == USER_ID, Project.id == project_id))
    ).scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    competency_names = await _competency_names_by_id(db)
    return _project_detail(project, competency_names)


# ============================================================================
# Endpoints: blog
# ============================================================================
@router.get("/blog", response_model=List[PublicBlogPost])
async def list_blog_posts(limit: int = Query(default=50, ge=1, le=100), db: AsyncSession = Depends(get_db)):
    posts = (
        await db.execute(
            select(Publication)
            .where(
                Publication.user_id == USER_ID,
                Publication.status == "published",
                Publication.platform == PORTAL_BLOG_PLATFORM,
            )
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
                Publication.user_id == USER_ID,
                Publication.slug == slug,
                Publication.status == "published",
                Publication.platform == PORTAL_BLOG_PLATFORM,
            )
        )
    ).scalar_one_or_none()
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return _blog_post(post)
