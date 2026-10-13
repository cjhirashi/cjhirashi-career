"""
Pydantic schemas - Career domain (v2), Dominio 2: Operativa de Búsqueda.

Covers: fit_scoring_factors, market_segments, role_narratives, search_plans,
networking_contacts, target_companies, vacancies, cv_versions,
cover_letter_versions, applications, application_interactions, interviews,
contact_interactions, networking_activities.
"""
from pydantic import BaseModel, BeforeValidator, Field, StringConstraints, computed_field, model_validator
from pydantic_core import PydanticCustomError
from typing import Annotated, Optional, List, Dict, Any, Literal
from datetime import date, datetime

from services.vacancy_stage import ProcessStage, VacancyStatus, vacancy_status_for


# ============================================================================
# FitScoringFactor
# ============================================================================

class FitScoringFactorBase(BaseModel):
    factor_name: str = Field(..., max_length=100)
    weight_percentage: Optional[int] = Field(None, ge=0, le=100)
    scoring_guide: Optional[str] = None
    display_order: Optional[int] = None


class FitScoringFactorCreate(FitScoringFactorBase):
    pass


class FitScoringFactorUpdate(BaseModel):
    factor_name: Optional[str] = Field(None, max_length=100)
    weight_percentage: Optional[int] = Field(None, ge=0, le=100)
    scoring_guide: Optional[str] = None
    display_order: Optional[int] = None


class FitScoringFactorResponse(FitScoringFactorBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# MarketSegment
# ============================================================================

MarketTypeLiteral = Literal["visible", "hidden"]


class MarketSegmentBase(BaseModel):
    market_type: Optional[MarketTypeLiteral] = None
    channel_name: Optional[str] = Field(None, max_length=255)
    channel_type: Optional[str] = Field(None, max_length=50)
    strategy_text: Optional[str] = None
    applications_made: int = 0
    responses_received: int = 0
    interviews_achieved: int = 0
    priority: Optional[int] = Field(None, ge=1, le=10)
    is_active: bool = True


class MarketSegmentCreate(MarketSegmentBase):
    pass


class MarketSegmentUpdate(BaseModel):
    market_type: Optional[MarketTypeLiteral] = None
    channel_name: Optional[str] = None
    channel_type: Optional[str] = None
    strategy_text: Optional[str] = None
    applications_made: Optional[int] = None
    responses_received: Optional[int] = None
    interviews_achieved: Optional[int] = None
    priority: Optional[int] = Field(None, ge=1, le=10)
    is_active: Optional[bool] = None


class MarketSegmentResponse(MarketSegmentBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# RoleNarrative
# ============================================================================

class RoleNarrativeBase(BaseModel):
    target_role_id: Optional[str] = None
    title: str = Field(..., max_length=255)
    usage_context: Optional[str] = Field(None, max_length=100)
    full_narrative: Optional[str] = None
    key_points: Optional[str] = None
    is_active: bool = True


class RoleNarrativeCreate(RoleNarrativeBase):
    pass


class RoleNarrativeUpdate(BaseModel):
    target_role_id: Optional[str] = None
    title: Optional[str] = Field(None, max_length=255)
    usage_context: Optional[str] = None
    full_narrative: Optional[str] = None
    key_points: Optional[str] = None
    is_active: Optional[bool] = None


class RoleNarrativeResponse(RoleNarrativeBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# SearchPlan
# ============================================================================

PlanStatusLiteral = Literal["not_started", "in_progress", "paused", "completed", "cancelled"]


class SearchPlanBase(BaseModel):
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    target_role_id: Optional[str] = None
    weekly_targets: Optional[Dict[str, Any]] = None
    primary_channels: Optional[str] = None
    target_cvs_sent: Optional[int] = None
    target_interviews: Optional[int] = None
    target_offers: Optional[int] = None
    plan_status: PlanStatusLiteral = "not_started"
    completion_percentage: Optional[int] = Field(default=0, ge=0, le=100)
    lessons_learned: Optional[str] = None


class SearchPlanCreate(SearchPlanBase):
    pass


class SearchPlanUpdate(BaseModel):
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    target_role_id: Optional[str] = None
    weekly_targets: Optional[Dict[str, Any]] = None
    primary_channels: Optional[str] = None
    target_cvs_sent: Optional[int] = None
    target_interviews: Optional[int] = None
    target_offers: Optional[int] = None
    plan_status: Optional[PlanStatusLiteral] = None
    completion_percentage: Optional[int] = Field(None, ge=0, le=100)
    lessons_learned: Optional[str] = None


class SearchPlanResponse(SearchPlanBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# NetworkingContact
# ============================================================================

RoleCategoryLiteral = Literal[
    "data_director", "automation_ai_peer", "manager_team_lead",
    "specialized_recruiter", "target_company_lead"
]
ContactStatusLiteral = Literal["pending", "contacted", "following_up", "converted"]


class NetworkingContactBase(BaseModel):
    name: str = Field(..., max_length=255)
    role_title: Optional[str] = Field(None, max_length=255)
    company_or_specialty: Optional[str] = Field(None, max_length=255)
    linkedin_url: Optional[str] = Field(None, max_length=500)
    email: Optional[str] = Field(None, max_length=255)
    role_category: Optional[RoleCategoryLiteral] = None
    contact_status: ContactStatusLiteral = "pending"
    how_originated: Optional[str] = None
    notes: Optional[str] = None


class NetworkingContactCreate(NetworkingContactBase):
    pass


class NetworkingContactUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    role_title: Optional[str] = None
    company_or_specialty: Optional[str] = None
    linkedin_url: Optional[str] = None
    email: Optional[str] = None
    role_category: Optional[RoleCategoryLiteral] = None
    contact_status: Optional[ContactStatusLiteral] = None
    how_originated: Optional[str] = None
    notes: Optional[str] = None


class NetworkingContactResponse(NetworkingContactBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# TargetCompany
# ============================================================================

class TargetCompanyBase(BaseModel):
    company_name: str = Field(..., max_length=255)
    tier: Optional[int] = None
    best_fit_role_id: Optional[str] = None
    company_size: Optional[str] = Field(None, max_length=50)
    salary_estimate: Optional[str] = Field(None, max_length=100)
    work_modality: Optional[str] = Field(None, max_length=100)
    target_market: Optional[str] = Field(None, max_length=100)
    weak_tie_contact_id: Optional[str] = None
    priority: Optional[str] = Field(None, max_length=10)
    status: Optional[str] = Field(None, max_length=30)
    notes: Optional[str] = None
    career_board_provider: Optional[Literal["greenhouse", "lever"]] = None
    career_board_token: Optional[str] = Field(None, max_length=100)
    industry_sector: Optional[str] = Field(None, max_length=100)
    company_culture: Optional[str] = None
    funding_stage: Optional[str] = Field(None, max_length=50)
    tech_stack: Optional[List[str]] = None
    company_website: Optional[str] = Field(None, max_length=500)
    linkedin_company_url: Optional[str] = Field(None, max_length=500)
    hiring_velocity: Optional[str] = Field(None, max_length=30)
    last_researched_at: Optional[date] = None
    review_score: Optional[float] = Field(None, ge=0)


class TargetCompanyCreate(TargetCompanyBase):
    pass


class TargetCompanyUpdate(BaseModel):
    company_name: Optional[str] = Field(None, max_length=255)
    tier: Optional[int] = None
    best_fit_role_id: Optional[str] = None
    company_size: Optional[str] = None
    salary_estimate: Optional[str] = None
    work_modality: Optional[str] = None
    target_market: Optional[str] = None
    weak_tie_contact_id: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    career_board_provider: Optional[Literal["greenhouse", "lever"]] = None
    career_board_token: Optional[str] = Field(None, max_length=100)
    industry_sector: Optional[str] = Field(None, max_length=100)
    company_culture: Optional[str] = None
    funding_stage: Optional[str] = Field(None, max_length=50)
    tech_stack: Optional[List[str]] = None
    company_website: Optional[str] = Field(None, max_length=500)
    linkedin_company_url: Optional[str] = Field(None, max_length=500)
    hiring_velocity: Optional[str] = Field(None, max_length=30)
    last_researched_at: Optional[date] = None
    review_score: Optional[float] = Field(None, ge=0)


class TargetCompanyResponse(TargetCompanyBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Vacancy
# ============================================================================

EvaluationLiteral = Literal["apply", "do_not_apply", "pending_review"]
ProcessStageLiteral = ProcessStage

# Spec 008: textos descriptivos largos de la vacante. Se recortan los bordes, el
# vacío pasa a None y el tope (RF-005) se mide DESPUÉS del recorte.
VACANCY_LONG_TEXT_MAX = 10_000


def _trim_or_none(value: Any) -> Any:
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return value  # no-str: que Pydantic lo rechace


VacancyLongText = Annotated[
    Optional[Annotated[str, StringConstraints(max_length=VACANCY_LONG_TEXT_MAX)]],
    BeforeValidator(_trim_or_none),
]


class VacancyBase(BaseModel):
    order_number: Optional[int] = None
    company: str = Field(..., max_length=255)
    target_company_id: Optional[str] = None
    exact_role: str = Field(..., max_length=255)
    vacancy_url: Optional[str] = Field(None, max_length=500)
    source: Optional[str] = Field(None, max_length=50)
    found_date: Optional[date] = None
    fit_percentage: Optional[int] = Field(None, ge=0, le=100)
    track_category: Optional[str] = Field(None, max_length=50)
    recommended_cv_version: Optional[str] = Field(None, max_length=100)
    analysis_notes: Optional[str] = None
    evaluation: EvaluationLiteral = "pending_review"
    is_active: bool = True
    location: Optional[str] = Field(None, max_length=255)
    work_modality: Optional[str] = Field(None, max_length=100)
    seniority_level: Optional[str] = Field(None, max_length=50)
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    required_skills: Optional[List[str]] = None
    years_experience_required: Optional[int] = None
    posted_date: Optional[date] = None
    process_stage: ProcessStageLiteral = "not_applied"
    priority: Optional[str] = Field(None, max_length=10)
    contracting_model: Optional[str] = Field(None, max_length=50)
    contact_id: Optional[str] = None
    company_overview: VacancyLongText = None
    candidate_profile: VacancyLongText = None
    offer_summary: VacancyLongText = None
    work_culture: VacancyLongText = None


class VacancyCreate(VacancyBase):
    pass


class VacancyUpdate(BaseModel):
    order_number: Optional[int] = None
    company: Optional[str] = Field(None, max_length=255)
    target_company_id: Optional[str] = None
    exact_role: Optional[str] = Field(None, max_length=255)
    vacancy_url: Optional[str] = None
    source: Optional[str] = None
    found_date: Optional[date] = None
    fit_percentage: Optional[int] = Field(None, ge=0, le=100)
    track_category: Optional[str] = None
    recommended_cv_version: Optional[str] = None
    analysis_notes: Optional[str] = None
    evaluation: Optional[EvaluationLiteral] = None
    is_active: Optional[bool] = None
    location: Optional[str] = None
    work_modality: Optional[str] = None
    seniority_level: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    required_skills: Optional[List[str]] = None
    years_experience_required: Optional[int] = None
    posted_date: Optional[date] = None
    process_stage: Optional[ProcessStageLiteral] = None
    priority: Optional[str] = None
    contracting_model: Optional[str] = None
    contact_id: Optional[str] = None
    company_overview: VacancyLongText = None
    candidate_profile: VacancyLongText = None
    offer_summary: VacancyLongText = None
    work_culture: VacancyLongText = None

    @model_validator(mode="after")
    def _process_stage_not_null(self):
        # Omitir la etapa es válido (no cambia); enviarla como null no (RF-002).
        if "process_stage" in self.model_fields_set and self.process_stage is None:
            # PydanticCustomError (no ValueError): su detalle es serializable por el
            # handler global de 422; un ValueError dejaba un objeto en ctx -> 500.
            raise PydanticCustomError("process_stage_not_null", "process_stage no puede ser null")
        return self


class VacancyResponse(VacancyBase):
    id: str
    user_id: str
    process_stage_updated_at: datetime
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def vacancy_status(self) -> VacancyStatus:
        return vacancy_status_for(self.process_stage)

    class Config:
        from_attributes = True


# ============================================================================
# CVVersion
# ============================================================================

VersionStatusLiteral = Literal["draft", "approved", "final"]


class CVVersionBase(BaseModel):
    target_role_id: Optional[str] = None
    title: str = Field(..., max_length=255)
    length_pages: Optional[int] = None
    status: VersionStatusLiteral = "draft"
    content: Optional[str] = None
    target_vacancy_ids: Optional[List[str]] = None
    file_upload_id: Optional[str] = None


class CVVersionCreate(CVVersionBase):
    pass


class CVVersionUpdate(BaseModel):
    target_role_id: Optional[str] = None
    title: Optional[str] = Field(None, max_length=255)
    length_pages: Optional[int] = None
    status: Optional[VersionStatusLiteral] = None
    content: Optional[str] = None
    target_vacancy_ids: Optional[List[str]] = None
    file_upload_id: Optional[str] = None


class CVVersionResponse(CVVersionBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# CoverLetterVersion
# ============================================================================

class CoverLetterVersionBase(BaseModel):
    target_role_id: Optional[str] = None
    target_vacancy_id: Optional[str] = None
    title: str = Field(..., max_length=255)
    status: VersionStatusLiteral = "draft"
    body_content: Optional[str] = None
    file_upload_id: Optional[str] = None


class CoverLetterVersionCreate(CoverLetterVersionBase):
    pass


class CoverLetterVersionUpdate(BaseModel):
    target_role_id: Optional[str] = None
    target_vacancy_id: Optional[str] = None
    title: Optional[str] = Field(None, max_length=255)
    status: Optional[VersionStatusLiteral] = None
    body_content: Optional[str] = None
    file_upload_id: Optional[str] = None


class CoverLetterVersionResponse(CoverLetterVersionBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Application
# ============================================================================

CurrentStatusLiteral = Literal["applied", "in_process", "offer", "rejected", "archived"]
FinalResultLiteral = Literal["offer_accepted", "offer_rejected", "rejected", "negotiating"]


class ApplicationBase(BaseModel):
    vacancy_id: str
    applied_at: Optional[datetime] = None
    cv_version_id: Optional[str] = None
    cover_letter_version_id: Optional[str] = None
    current_status: CurrentStatusLiteral = "applied"
    recruiter_contact_id: Optional[str] = None
    final_result: Optional[FinalResultLiteral] = None


class ApplicationCreate(ApplicationBase):
    pass


class ApplicationUpdate(BaseModel):
    vacancy_id: Optional[str] = None
    applied_at: Optional[datetime] = None
    cv_version_id: Optional[str] = None
    cover_letter_version_id: Optional[str] = None
    current_status: Optional[CurrentStatusLiteral] = None
    recruiter_contact_id: Optional[str] = None
    final_result: Optional[FinalResultLiteral] = None


class ApplicationResponse(ApplicationBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# ApplicationInteraction
# ============================================================================

class ApplicationInteractionBase(BaseModel):
    application_id: str
    interaction_at: Optional[datetime] = None
    channel: Optional[str] = Field(None, max_length=50)
    content_sent: Optional[str] = None
    response_received: Optional[str] = None
    status: Optional[str] = Field(None, max_length=50)


class ApplicationInteractionCreate(ApplicationInteractionBase):
    pass


class ApplicationInteractionUpdate(BaseModel):
    interaction_at: Optional[datetime] = None
    channel: Optional[str] = None
    content_sent: Optional[str] = None
    response_received: Optional[str] = None
    status: Optional[str] = None


class ApplicationInteractionResponse(ApplicationInteractionBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Interview
# ============================================================================

OverallImpressionLiteral = Literal["very_positive", "positive", "neutral", "negative"]
InterviewResultLiteral = Literal["pending", "advanced", "rejected", "under_consideration"]


class InterviewBase(BaseModel):
    application_id: str
    interview_type: Optional[str] = Field(None, max_length=50)
    scheduled_at: Optional[datetime] = None
    interviewers: Optional[str] = None
    questions_asked: Optional[str] = None
    answers_given: Optional[str] = None
    feedback_received: Optional[str] = None
    overall_impression: Optional[OverallImpressionLiteral] = None
    narrative_used_id: Optional[str] = None
    interview_result: Optional[InterviewResultLiteral] = None


class InterviewCreate(InterviewBase):
    pass


class InterviewUpdate(BaseModel):
    interview_type: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    interviewers: Optional[str] = None
    questions_asked: Optional[str] = None
    answers_given: Optional[str] = None
    feedback_received: Optional[str] = None
    overall_impression: Optional[OverallImpressionLiteral] = None
    narrative_used_id: Optional[str] = None
    interview_result: Optional[InterviewResultLiteral] = None


class InterviewResponse(InterviewBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# ContactInteraction
# ============================================================================

class ContactInteractionBase(BaseModel):
    contact_id: str
    related_vacancy_id: Optional[str] = None
    interaction_at: Optional[datetime] = None
    channel: Optional[str] = Field(None, max_length=50)
    content_sent: Optional[str] = None
    response_received: Optional[str] = None
    status: Optional[str] = Field(None, max_length=50)
    generated_opportunity: bool = False


class ContactInteractionCreate(ContactInteractionBase):
    pass


class ContactInteractionUpdate(BaseModel):
    related_vacancy_id: Optional[str] = None
    interaction_at: Optional[datetime] = None
    channel: Optional[str] = None
    content_sent: Optional[str] = None
    response_received: Optional[str] = None
    status: Optional[str] = None
    generated_opportunity: Optional[bool] = None


class ContactInteractionResponse(ContactInteractionBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# NetworkingActivity
# ============================================================================

CategoryLiteral = Literal["give_value_70", "share_learning_20", "talk_about_you_10"]


class NetworkingActivityBase(BaseModel):
    category: Optional[CategoryLiteral] = None
    activity_type: str = Field(..., max_length=255)
    concrete_action: Optional[str] = None
    example: Optional[str] = None
    frequency_description: Optional[str] = Field(None, max_length=100)
    times_completed: int = 0
    is_active: bool = True


class NetworkingActivityCreate(NetworkingActivityBase):
    pass


class NetworkingActivityUpdate(BaseModel):
    category: Optional[CategoryLiteral] = None
    activity_type: Optional[str] = Field(None, max_length=255)
    concrete_action: Optional[str] = None
    example: Optional[str] = None
    frequency_description: Optional[str] = None
    times_completed: Optional[int] = None
    is_active: Optional[bool] = None


class NetworkingActivityResponse(NetworkingActivityBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
