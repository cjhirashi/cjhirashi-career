"""
Pydantic schemas - Career domain (v2), Dominio 1: Identidad Profesional.

Covers: differentiators, identity, identity_reflections, competencies,
certifications, target_roles, work_history, achievements, star_stories,
career_reviews, role_gap_analysis, projects.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal, Union
from datetime import date, datetime


# ============================================================================
# Differentiator
# ============================================================================

class DifferentiatorBase(BaseModel):
    pillar_name: str = Field(..., max_length=255)
    pillar_description: Optional[str] = None
    strengths: Optional[str] = None
    evidence: Optional[str] = None
    is_active: bool = True


class DifferentiatorCreate(DifferentiatorBase):
    pass


class DifferentiatorUpdate(BaseModel):
    pillar_name: Optional[str] = Field(None, max_length=255)
    pillar_description: Optional[str] = None
    strengths: Optional[str] = None
    evidence: Optional[str] = None
    is_active: Optional[bool] = None


class DifferentiatorResponse(DifferentiatorBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Identity
# ============================================================================

class IdentityBase(BaseModel):
    professional_tagline: Optional[str] = Field(None, max_length=255)
    bio_summary: Optional[str] = None
    unique_value_proposition: Optional[str] = None


class IdentityCreate(IdentityBase):
    pass


class IdentityUpdate(IdentityBase):
    pass


class IdentityResponse(IdentityBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# IdentityReflection
# ============================================================================

DimensionLiteral = Literal["passion", "profession", "vocation", "mission"]


class IdentityReflectionBase(BaseModel):
    dimension: DimensionLiteral
    content: Optional[str] = None
    tags: Optional[str] = None


class IdentityReflectionCreate(IdentityReflectionBase):
    pass


class IdentityReflectionUpdate(BaseModel):
    content: Optional[str] = None
    tags: Optional[str] = None


class IdentityReflectionResponse(IdentityReflectionBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Competency
# ============================================================================

CompetencyTypeLiteral = Literal["technical", "transferable", "business"]


class CompetencyBase(BaseModel):
    name: str = Field(..., max_length=255)
    type: CompetencyTypeLiteral
    category: Optional[str] = Field(None, max_length=100)
    level: Optional[str] = Field(None, max_length=50)
    years_of_experience: Optional[float] = None
    practice_start_date: Optional[date] = None
    context_libraries: Optional[List[Any]] = None
    depth_description: Optional[str] = None
    market_gaps: Optional[str] = None
    honesty_note: Optional[str] = None
    aligned_differentiator_ids: Optional[List[int]] = None
    proficiency_score: Optional[int] = Field(None, ge=0, le=100)
    is_highlighted: bool = False


class CompetencyCreate(CompetencyBase):
    pass


class CompetencyUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    type: Optional[CompetencyTypeLiteral] = None
    category: Optional[str] = None
    level: Optional[str] = None
    years_of_experience: Optional[float] = None
    practice_start_date: Optional[date] = None
    context_libraries: Optional[List[Any]] = None
    depth_description: Optional[str] = None
    market_gaps: Optional[str] = None
    honesty_note: Optional[str] = None
    aligned_differentiator_ids: Optional[List[int]] = None
    proficiency_score: Optional[int] = Field(None, ge=0, le=100)
    is_highlighted: Optional[bool] = None


class CompetencyResponse(CompetencyBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Certification
# ============================================================================

class CertificationBase(BaseModel):
    name: str = Field(..., max_length=255)
    institution: Optional[str] = Field(None, max_length=255)
    year: Optional[int] = None
    description: Optional[str] = None
    related_competency_id: Optional[int] = None


class CertificationCreate(CertificationBase):
    pass


class CertificationUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    institution: Optional[str] = None
    year: Optional[int] = None
    description: Optional[str] = None
    related_competency_id: Optional[int] = None


class CertificationResponse(CertificationBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# TargetRole
# ============================================================================

class TargetRoleBase(BaseModel):
    role_name: str = Field(..., max_length=255)
    priority_order: Optional[int] = Field(None, ge=1, le=3)
    salary_median: Optional[int] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    years_experience_required: Optional[int] = None
    description: Optional[str] = None
    market_active_vacancies: Optional[int] = None
    market_validated_at: Optional[date] = None
    market_sources: Optional[List[Any]] = None
    current_accessibility: Optional[str] = Field(None, max_length=100)
    key_requirements: Optional[str] = None
    is_active: bool = True


class TargetRoleCreate(TargetRoleBase):
    pass


class TargetRoleUpdate(BaseModel):
    role_name: Optional[str] = Field(None, max_length=255)
    priority_order: Optional[int] = Field(None, ge=1, le=3)
    salary_median: Optional[int] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    years_experience_required: Optional[int] = None
    description: Optional[str] = None
    market_active_vacancies: Optional[int] = None
    market_validated_at: Optional[date] = None
    market_sources: Optional[List[Any]] = None
    current_accessibility: Optional[str] = None
    key_requirements: Optional[str] = None
    is_active: Optional[bool] = None


class TargetRoleResponse(TargetRoleBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# WorkHistory
# ============================================================================

class WorkHistoryBase(BaseModel):
    company: str = Field(..., max_length=255)
    role_title: str = Field(..., max_length=255)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    people_managed: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    narrative: Optional[str] = None
    achievements: Optional[str] = None
    key_metrics: Optional[Dict[str, Any]] = None
    learnings: Optional[str] = None
    contract_type: Optional[str] = Field(None, max_length=50)
    industry_sector: Optional[str] = Field(None, max_length=100)


class WorkHistoryCreate(WorkHistoryBase):
    pass


class WorkHistoryUpdate(BaseModel):
    company: Optional[str] = Field(None, max_length=255)
    role_title: Optional[str] = Field(None, max_length=255)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    people_managed: Optional[str] = None
    description: Optional[str] = None
    narrative: Optional[str] = None
    achievements: Optional[str] = None
    key_metrics: Optional[Dict[str, Any]] = None
    learnings: Optional[str] = None
    contract_type: Optional[str] = None
    industry_sector: Optional[str] = None


class WorkHistoryResponse(WorkHistoryBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Achievement
# ============================================================================

EvidenceTypeLiteral = Literal["direct_account", "public_backed"]


class AchievementBase(BaseModel):
    title: str = Field(..., max_length=255)
    work_history_id: Optional[int] = None
    context: Optional[Dict[str, Any]] = None
    challenge: Optional[str] = None
    solution: Optional[str] = None
    impact_metrics: Optional[Dict[str, Any]] = None
    evidence_type: Optional[EvidenceTypeLiteral] = None
    documentation_urls: Optional[str] = None
    executive_storytelling: Optional[str] = None
    demonstrated_competency_ids: Optional[List[int]] = None
    visible_on_cv: bool = True
    visible_in_interview: bool = True
    visible_on_portal: bool = False


class AchievementCreate(AchievementBase):
    pass


class AchievementUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    work_history_id: Optional[int] = None
    context: Optional[Dict[str, Any]] = None
    challenge: Optional[str] = None
    solution: Optional[str] = None
    impact_metrics: Optional[Dict[str, Any]] = None
    evidence_type: Optional[EvidenceTypeLiteral] = None
    documentation_urls: Optional[str] = None
    executive_storytelling: Optional[str] = None
    demonstrated_competency_ids: Optional[List[int]] = None
    visible_on_cv: Optional[bool] = None
    visible_in_interview: Optional[bool] = None
    visible_on_portal: Optional[bool] = None


class AchievementResponse(AchievementBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# StarStory
# ============================================================================

class StarStoryBase(BaseModel):
    title: str = Field(..., max_length=255)
    duration_seconds: Optional[int] = Field(None, ge=60, le=90)
    narrative: Optional[str] = None
    key_points: Optional[str] = None
    achievement_id: Optional[int] = None
    cross_pattern: Optional[str] = Field(None, max_length=255)
    role_application: Optional[str] = None
    times_practiced: int = 0
    active_in_interviews: bool = True


class StarStoryCreate(StarStoryBase):
    pass


class StarStoryUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    duration_seconds: Optional[int] = Field(None, ge=60, le=90)
    narrative: Optional[str] = None
    key_points: Optional[str] = None
    achievement_id: Optional[int] = None
    cross_pattern: Optional[str] = None
    role_application: Optional[str] = None
    times_practiced: Optional[int] = None
    active_in_interviews: Optional[bool] = None


class StarStoryResponse(StarStoryBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# CareerReview
# ============================================================================

ReviewTypeLiteral = Literal["gap_analysis", "transition_decision", "quarterly_review"]
TrackingStatusLiteral = Literal["active", "completed", "paused"]


class CareerReviewBase(BaseModel):
    review_date: Optional[date] = None
    review_type: Optional[ReviewTypeLiteral] = None
    context: Optional[str] = None
    decision_or_finding: Optional[str] = None
    result_or_learning: Optional[str] = None
    action_items: Optional[str] = None
    tracking_status: TrackingStatusLiteral = "active"


class CareerReviewCreate(CareerReviewBase):
    pass


class CareerReviewUpdate(BaseModel):
    review_date: Optional[date] = None
    review_type: Optional[ReviewTypeLiteral] = None
    context: Optional[str] = None
    decision_or_finding: Optional[str] = None
    result_or_learning: Optional[str] = None
    action_items: Optional[str] = None
    tracking_status: Optional[TrackingStatusLiteral] = None


class CareerReviewResponse(CareerReviewBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# RoleGapAnalysis
# ============================================================================

SeverityLiteral = Literal["critical", "high", "medium", "low"]
ViabilityLiteral = Literal["viable", "viable_with_caveats", "not_viable"]
ClosureStatusLiteral = Literal["not_started", "in_progress", "completed", "paused"]


class RoleGapAnalysisBase(BaseModel):
    target_role_id: int
    gap_name: str = Field(..., max_length=255)
    severity: Optional[SeverityLiteral] = None
    market_requirement: Optional[str] = None
    closing_plan: Optional[str] = None
    viability: Optional[ViabilityLiteral] = None
    closure_status: ClosureStatusLiteral = "not_started"


class RoleGapAnalysisCreate(RoleGapAnalysisBase):
    pass


class RoleGapAnalysisUpdate(BaseModel):
    target_role_id: Optional[int] = None
    gap_name: Optional[str] = Field(None, max_length=255)
    severity: Optional[SeverityLiteral] = None
    market_requirement: Optional[str] = None
    closing_plan: Optional[str] = None
    viability: Optional[ViabilityLiteral] = None
    closure_status: Optional[ClosureStatusLiteral] = None


class RoleGapAnalysisResponse(RoleGapAnalysisBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Project
# ============================================================================

ProjectStatusLiteral = Literal["active", "in_development", "archived"]


class ProjectBase(BaseModel):
    title: str = Field(..., max_length=255)
    category: Optional[str] = Field(None, max_length=50)
    industry: Optional[str] = Field(None, max_length=100)
    year: Optional[int] = None
    card_summary: Optional[str] = Field(None, max_length=500)
    detailed_summary: Optional[str] = None
    problem: Optional[str] = None
    solution: Optional[str] = None
    architecture: Optional[str] = None
    tech_stack: Optional[str] = None
    metrics: Optional[Union[List[Any], Dict[str, Any]]] = None
    approach_steps: Optional[str] = None
    results: Optional[Union[List[Any], Dict[str, Any]]] = None
    github_url: Optional[str] = Field(None, max_length=500)
    demo_url: Optional[str] = Field(None, max_length=500)
    repo_structure: Optional[str] = None
    evidence_sources: Optional[str] = None
    releases: Optional[List[Any]] = None
    status: ProjectStatusLiteral = "active"
    is_featured: bool = False


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    category: Optional[str] = None
    industry: Optional[str] = None
    year: Optional[int] = None
    card_summary: Optional[str] = None
    detailed_summary: Optional[str] = None
    problem: Optional[str] = None
    solution: Optional[str] = None
    architecture: Optional[str] = None
    tech_stack: Optional[str] = None
    metrics: Optional[Union[List[Any], Dict[str, Any]]] = None
    approach_steps: Optional[str] = None
    results: Optional[Union[List[Any], Dict[str, Any]]] = None
    github_url: Optional[str] = None
    demo_url: Optional[str] = None
    repo_structure: Optional[str] = None
    evidence_sources: Optional[str] = None
    releases: Optional[List[Any]] = None
    status: Optional[ProjectStatusLiteral] = None
    is_featured: Optional[bool] = None


class ProjectResponse(ProjectBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
