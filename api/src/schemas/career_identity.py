"""
Pydantic schemas - Career domain (v2), Dominio 1: Identidad Profesional.

Covers: personal_profile, differentiators, identity, identity_reflections, competencies,
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
    notes: Optional[str] = None


class DifferentiatorCreate(DifferentiatorBase):
    pass
    notes: Optional[str] = None


class DifferentiatorUpdate(BaseModel):
    pillar_name: Optional[str] = Field(None, max_length=255)
    pillar_description: Optional[str] = None
    strengths: Optional[str] = None
    evidence: Optional[str] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class DifferentiatorResponse(DifferentiatorBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    notes: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================================
# Identity
# ============================================================================

class IdentityBase(BaseModel):
    professional_tagline: Optional[str] = Field(None, max_length=255)
    bio_summary: Optional[str] = None
    unique_value_proposition: Optional[str] = None
    notes: Optional[str] = None


class IdentityCreate(IdentityBase):
    pass
    notes: Optional[str] = None


class IdentityUpdate(IdentityBase):
    pass
    notes: Optional[str] = None


class IdentityResponse(IdentityBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    notes: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================================
# PersonalProfile — ficha biográfica singleton (referencia del gestor)
# ============================================================================

class PersonalProfileBase(BaseModel):
    full_name: str = Field(..., max_length=255)
    preferred_name: Optional[str] = Field(None, max_length=255)
    date_of_birth: Optional[date] = None
    nationality: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=255)
    country: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=40)
    email: Optional[str] = Field(None, max_length=255)
    languages: Optional[str] = None
    work_authorization: Optional[str] = None
    notes: Optional[str] = None


class PersonalProfileCreate(PersonalProfileBase):
    pass


class PersonalProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=255)
    preferred_name: Optional[str] = Field(None, max_length=255)
    date_of_birth: Optional[date] = None
    nationality: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=255)
    country: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=40)
    email: Optional[str] = Field(None, max_length=255)
    languages: Optional[str] = None
    work_authorization: Optional[str] = None
    notes: Optional[str] = None


class PersonalProfileResponse(PersonalProfileBase):
    id: str
    user_id: str
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
    notes: Optional[str] = None


class IdentityReflectionCreate(IdentityReflectionBase):
    pass
    notes: Optional[str] = None


class IdentityReflectionUpdate(BaseModel):
    content: Optional[str] = None
    tags: Optional[str] = None
    notes: Optional[str] = None


class IdentityReflectionResponse(IdentityReflectionBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    notes: Optional[str] = None

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
    aligned_differentiator_ids: Optional[List[str]] = None
    proficiency_score: Optional[int] = Field(None, ge=0, le=100)
    is_highlighted: bool = False
    featured_on_home: bool = False
    notes: Optional[str] = None


class CompetencyCreate(CompetencyBase):
    pass
    notes: Optional[str] = None


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
    aligned_differentiator_ids: Optional[List[str]] = None
    proficiency_score: Optional[int] = Field(None, ge=0, le=100)
    is_highlighted: Optional[bool] = None
    featured_on_home: Optional[bool] = None
    notes: Optional[str] = None


class CompetencyResponse(CompetencyBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    notes: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================================
# Certification
# ============================================================================

CertificationStatusLiteral = Literal["pending", "in_progress", "completed"]


class CertificationBase(BaseModel):
    name: str = Field(..., max_length=255)
    institution: Optional[str] = Field(None, max_length=255)
    year: Optional[int] = None
    description: Optional[str] = None
    syllabus: Optional[str] = None
    document_url: Optional[str] = Field(None, max_length=1000)
    status: CertificationStatusLiteral = "pending"
    related_competency_id: Optional[str] = None
    notes: Optional[str] = None


class CertificationCreate(CertificationBase):
    pass
    notes: Optional[str] = None


class CertificationUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    institution: Optional[str] = None
    year: Optional[int] = None
    description: Optional[str] = None
    syllabus: Optional[str] = None
    document_url: Optional[str] = Field(None, max_length=1000)
    status: Optional[CertificationStatusLiteral] = None
    related_competency_id: Optional[str] = None
    notes: Optional[str] = None


class CertificationResponse(CertificationBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    notes: Optional[str] = None

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
    notes: Optional[str] = None


class TargetRoleCreate(TargetRoleBase):
    pass
    notes: Optional[str] = None


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
    notes: Optional[str] = None


class TargetRoleResponse(TargetRoleBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    notes: Optional[str] = None

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
    notes: Optional[str] = None


class WorkHistoryCreate(WorkHistoryBase):
    pass
    notes: Optional[str] = None


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
    notes: Optional[str] = None


class WorkHistoryResponse(WorkHistoryBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    notes: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================================
# Achievement
# ============================================================================

EvidenceTypeLiteral = Literal["direct_account", "public_backed"]


class AchievementBase(BaseModel):
    title: str = Field(..., max_length=255)
    work_history_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    challenge: Optional[str] = None
    solution: Optional[str] = None
    impact_metrics: Optional[Dict[str, Any]] = None
    evidence_type: Optional[EvidenceTypeLiteral] = None
    documentation_urls: Optional[str] = None
    executive_storytelling: Optional[str] = None
    demonstrated_competency_ids: Optional[List[str]] = None
    visible_on_cv: bool = True
    visible_in_interview: bool = True
    visible_on_portal: bool = False
    notes: Optional[str] = None


class AchievementCreate(AchievementBase):
    pass
    notes: Optional[str] = None


class AchievementUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    work_history_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    challenge: Optional[str] = None
    solution: Optional[str] = None
    impact_metrics: Optional[Dict[str, Any]] = None
    evidence_type: Optional[EvidenceTypeLiteral] = None
    documentation_urls: Optional[str] = None
    executive_storytelling: Optional[str] = None
    demonstrated_competency_ids: Optional[List[str]] = None
    visible_on_cv: Optional[bool] = None
    visible_in_interview: Optional[bool] = None
    visible_on_portal: Optional[bool] = None
    notes: Optional[str] = None


class AchievementResponse(AchievementBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    notes: Optional[str] = None

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
    achievement_id: Optional[str] = None
    cross_pattern: Optional[str] = Field(None, max_length=255)
    role_application: Optional[str] = None
    times_practiced: int = 0
    active_in_interviews: bool = True
    notes: Optional[str] = None


class StarStoryCreate(StarStoryBase):
    pass
    notes: Optional[str] = None


class StarStoryUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    duration_seconds: Optional[int] = Field(None, ge=60, le=90)
    narrative: Optional[str] = None
    key_points: Optional[str] = None
    achievement_id: Optional[str] = None
    cross_pattern: Optional[str] = None
    role_application: Optional[str] = None
    times_practiced: Optional[int] = None
    active_in_interviews: Optional[bool] = None
    notes: Optional[str] = None


class StarStoryResponse(StarStoryBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    notes: Optional[str] = None

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
    notes: Optional[str] = None


class CareerReviewCreate(CareerReviewBase):
    pass
    notes: Optional[str] = None


class CareerReviewUpdate(BaseModel):
    review_date: Optional[date] = None
    review_type: Optional[ReviewTypeLiteral] = None
    context: Optional[str] = None
    decision_or_finding: Optional[str] = None
    result_or_learning: Optional[str] = None
    action_items: Optional[str] = None
    tracking_status: Optional[TrackingStatusLiteral] = None
    notes: Optional[str] = None


class CareerReviewResponse(CareerReviewBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    notes: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================================
# RoleGapAnalysis
# ============================================================================

SeverityLiteral = Literal["critical", "high", "medium", "low"]
ViabilityLiteral = Literal["viable", "viable_with_caveats", "not_viable"]
ClosureStatusLiteral = Literal["not_started", "in_progress", "completed", "paused"]


class RoleGapAnalysisBase(BaseModel):
    target_role_id: str
    gap_name: str = Field(..., max_length=255)
    severity: Optional[SeverityLiteral] = None
    market_requirement: Optional[str] = None
    closing_plan: Optional[str] = None
    viability: Optional[ViabilityLiteral] = None
    closure_status: ClosureStatusLiteral = "not_started"
    notes: Optional[str] = None


class RoleGapAnalysisCreate(RoleGapAnalysisBase):
    pass
    notes: Optional[str] = None


class RoleGapAnalysisUpdate(BaseModel):
    target_role_id: Optional[str] = None
    gap_name: Optional[str] = Field(None, max_length=255)
    severity: Optional[SeverityLiteral] = None
    market_requirement: Optional[str] = None
    closing_plan: Optional[str] = None
    viability: Optional[ViabilityLiteral] = None
    closure_status: Optional[ClosureStatusLiteral] = None
    notes: Optional[str] = None


class RoleGapAnalysisResponse(RoleGapAnalysisBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    notes: Optional[str] = None

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
    metric1_label: Optional[str] = Field(None, max_length=100)
    metric1_value: Optional[str] = Field(None, max_length=500)
    metric2_label: Optional[str] = Field(None, max_length=100)
    metric2_value: Optional[str] = Field(None, max_length=500)
    metric3_label: Optional[str] = Field(None, max_length=100)
    metric3_value: Optional[str] = Field(None, max_length=500)
    metric4_label: Optional[str] = Field(None, max_length=100)
    metric4_value: Optional[str] = Field(None, max_length=500)
    approach_steps: Optional[str] = None
    results: Optional[Union[List[Any], Dict[str, Any]]] = None
    github_url: Optional[str] = Field(None, max_length=500)
    demo_url: Optional[str] = Field(None, max_length=500)
    repo_structure: Optional[str] = None
    evidence_sources: Optional[str] = None
    releases: Optional[List[Any]] = None
    status: ProjectStatusLiteral = "active"
    is_featured: bool = False
    is_anchor: bool = False
    image_url: Optional[str] = Field(None, max_length=1024)
    notes: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass
    notes: Optional[str] = None


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
    metric1_label: Optional[str] = None
    metric1_value: Optional[str] = None
    metric2_label: Optional[str] = None
    metric2_value: Optional[str] = None
    metric3_label: Optional[str] = None
    metric3_value: Optional[str] = None
    metric4_label: Optional[str] = None
    metric4_value: Optional[str] = None
    approach_steps: Optional[str] = None
    results: Optional[Union[List[Any], Dict[str, Any]]] = None
    github_url: Optional[str] = None
    demo_url: Optional[str] = None
    repo_structure: Optional[str] = None
    evidence_sources: Optional[str] = None
    releases: Optional[List[Any]] = None
    status: Optional[ProjectStatusLiteral] = None
    is_featured: Optional[bool] = None
    is_anchor: Optional[bool] = None
    image_url: Optional[str] = None
    notes: Optional[str] = None


class ProjectResponse(ProjectBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    notes: Optional[str] = None

    class Config:
        from_attributes = True
