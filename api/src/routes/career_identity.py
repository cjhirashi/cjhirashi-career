"""
Career domain (v2), Dominio 1: Identidad Profesional.

Aggregates CRUD routers for: differentiators, identity, identity_reflections,
competencies, certifications, target_roles, work_history, achievements,
star_stories, career_reviews, role_gap_analysis, projects.
"""
# ============================================================================
# Imports
# ============================================================================
from fastapi import APIRouter

from models.differentiator import Differentiator
from models.identity import Identity
from models.identity_reflection import IdentityReflection
from models.competencies import Competency
from models.certification import Certification
from models.target_role import TargetRole
from models.work_history import WorkHistory
from models.achievement import Achievement
from models.star_story import StarStory
from models.career_review import CareerReview
from models.role_gap_analysis import RoleGapAnalysis
from models.project import Project

from schemas.career_identity import (
    DifferentiatorCreate, DifferentiatorUpdate, DifferentiatorResponse,
    IdentityCreate, IdentityUpdate, IdentityResponse,
    IdentityReflectionCreate, IdentityReflectionUpdate, IdentityReflectionResponse,
    CompetencyCreate, CompetencyUpdate, CompetencyResponse,
    CertificationCreate, CertificationUpdate, CertificationResponse,
    TargetRoleCreate, TargetRoleUpdate, TargetRoleResponse,
    WorkHistoryCreate, WorkHistoryUpdate, WorkHistoryResponse,
    AchievementCreate, AchievementUpdate, AchievementResponse,
    StarStoryCreate, StarStoryUpdate, StarStoryResponse,
    CareerReviewCreate, CareerReviewUpdate, CareerReviewResponse,
    RoleGapAnalysisCreate, RoleGapAnalysisUpdate, RoleGapAnalysisResponse,
    ProjectCreate, ProjectUpdate, ProjectResponse,
)

from routes.career_common import build_crud_router

# ============================================================================
# Router principal
# ============================================================================
router = APIRouter(prefix="/career", tags=["Career - Identity"])

# ============================================================================
# Identidad profesional
# ============================================================================
router.include_router(build_crud_router(
    prefix="/differentiators", tags=["Career - Identity"], model=Differentiator,
    create_schema=DifferentiatorCreate, update_schema=DifferentiatorUpdate,
    response_schema=DifferentiatorResponse, entity_name="differentiator",
))

router.include_router(build_crud_router(
    prefix="/identity", tags=["Career - Identity"], model=Identity,
    create_schema=IdentityCreate, update_schema=IdentityUpdate,
    response_schema=IdentityResponse, entity_name="identity",
))

router.include_router(build_crud_router(
    prefix="/identity-reflections", tags=["Career - Identity"], model=IdentityReflection,
    create_schema=IdentityReflectionCreate, update_schema=IdentityReflectionUpdate,
    response_schema=IdentityReflectionResponse, entity_name="identity reflection",
))

# ============================================================================
# Competencias y certificaciones
# ============================================================================
router.include_router(build_crud_router(
    prefix="/competencies", tags=["Career - Identity"], model=Competency,
    create_schema=CompetencyCreate, update_schema=CompetencyUpdate,
    response_schema=CompetencyResponse, entity_name="competency",
))

router.include_router(build_crud_router(
    prefix="/certifications", tags=["Career - Identity"], model=Certification,
    create_schema=CertificationCreate, update_schema=CertificationUpdate,
    response_schema=CertificationResponse, entity_name="certification",
))

# ============================================================================
# Roles y experiencia laboral
# ============================================================================
router.include_router(build_crud_router(
    prefix="/target-roles", tags=["Career - Identity"], model=TargetRole,
    create_schema=TargetRoleCreate, update_schema=TargetRoleUpdate,
    response_schema=TargetRoleResponse, entity_name="target role",
))

router.include_router(build_crud_router(
    prefix="/work-history", tags=["Career - Identity"], model=WorkHistory,
    create_schema=WorkHistoryCreate, update_schema=WorkHistoryUpdate,
    response_schema=WorkHistoryResponse, entity_name="work history entry",
))

# ============================================================================
# Logros, narrativas y revisiones de carrera
# ============================================================================
router.include_router(build_crud_router(
    prefix="/achievements", tags=["Career - Identity"], model=Achievement,
    create_schema=AchievementCreate, update_schema=AchievementUpdate,
    response_schema=AchievementResponse, entity_name="achievement",
))

router.include_router(build_crud_router(
    prefix="/star-stories", tags=["Career - Identity"], model=StarStory,
    create_schema=StarStoryCreate, update_schema=StarStoryUpdate,
    response_schema=StarStoryResponse, entity_name="STAR story",
))

router.include_router(build_crud_router(
    prefix="/career-reviews", tags=["Career - Identity"], model=CareerReview,
    create_schema=CareerReviewCreate, update_schema=CareerReviewUpdate,
    response_schema=CareerReviewResponse, entity_name="career review",
))

router.include_router(build_crud_router(
    prefix="/role-gap-analysis", tags=["Career - Identity"], model=RoleGapAnalysis,
    create_schema=RoleGapAnalysisCreate, update_schema=RoleGapAnalysisUpdate,
    response_schema=RoleGapAnalysisResponse, entity_name="role gap analysis",
))

# ============================================================================
# Proyectos
# ============================================================================
router.include_router(build_crud_router(
    prefix="/projects", tags=["Career - Identity"], model=Project,
    create_schema=ProjectCreate, update_schema=ProjectUpdate,
    response_schema=ProjectResponse, entity_name="project",
))
