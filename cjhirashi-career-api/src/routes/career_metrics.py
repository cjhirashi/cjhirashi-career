"""
Career domain (v2) - Metrics.

Read-only endpoint over `search_metrics_view`, a SQL view computed from
`applications` and `interviews` (never captured/edited by hand). No
SQLAlchemy ORM model is mapped for the view (Postgres views have no
primary key), so it is queried directly with parametrized SQL, still
scoped to the authenticated user.
"""
# ============================================================================
# Imports
# ============================================================================
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from middleware.auth import get_current_user
from models.application import Application
from models.application_interaction import ApplicationInteraction
from models.contact_interaction import ContactInteraction
from models.fit_scoring_factor import FitScoringFactor
from models.interview import Interview
from models.market_segment import MarketSegment
from models.networking_activity import NetworkingActivity
from models.networking_contact import NetworkingContact
from models.search_plan import SearchPlan
from models.search_platform import SearchPlatform
from models.target_company import TargetCompany
from models.user import User
from models.vacancy import Vacancy
from schemas.career_metrics import (
    CountBreakdown,
    FitFactorMetric,
    FunnelStage,
    KpiMetric,
    MarketSegmentMetric,
    PlatformResult,
    RateMetric,
    SearchMetricsWeekResponse,
    SearchOverviewResponse,
    SearchPlanMetric,
)

# ============================================================================
# Router principal
# ============================================================================
router = APIRouter(prefix="/career/metrics", tags=["Career - Metrics"])


# ============================================================================
# Helpers de agregación
# ============================================================================
async def _count_by(db: AsyncSession, user_id: str, model, column) -> List[CountBreakdown]:
    """Generic `SELECT column, COUNT(*) ... GROUP BY column` for one user."""
    stmt = (
        select(column, func.count())
        .where(model.user_id == user_id)
        .group_by(column)
        .order_by(func.count().desc())
    )
    result = await db.execute(stmt)
    return [CountBreakdown(label=str(label) if label is not None else "Sin definir", count=count) for label, count in result.all()]


async def _sum_by(db: AsyncSession, user_id: str, model, group_column, sum_column) -> List[CountBreakdown]:
    """`SELECT group_column, SUM(sum_column) ... GROUP BY group_column` for one user."""
    stmt = (
        select(group_column, func.coalesce(func.sum(sum_column), 0))
        .where(model.user_id == user_id)
        .group_by(group_column)
        .order_by(func.coalesce(func.sum(sum_column), 0).desc())
    )
    result = await db.execute(stmt)
    return [CountBreakdown(label=str(label) if label is not None else "Sin definir", count=int(total)) for label, total in result.all()]


async def _response_rate(db: AsyncSession, user_id: str, model, response_column) -> RateMetric:
    """Out of every row for this user, how many have a non-empty `response_column`
    (a Text field holding the response content itself, not a boolean flag)."""
    total = (await db.execute(select(func.count()).select_from(model).where(model.user_id == user_id))).scalar_one()
    positive = (
        await db.execute(
            select(func.count())
            .select_from(model)
            .where(model.user_id == user_id, response_column.is_not(None), response_column != "")
        )
    ).scalar_one()
    rate = round(positive / total * 100, 1) if total > 0 else None
    return RateMetric(total=total, positive=positive, rate_percentage=rate)


def _kpi(label: str, numerator: int, denominator: int, detail: str | None = None) -> KpiMetric:
    rate = round(numerator / denominator * 100, 1) if denominator > 0 else None
    return KpiMetric(label=label, value_percentage=rate, detail=detail or f"{numerator} de {denominator}")


def _count_for_label(breakdown: List[CountBreakdown], label: str) -> int:
    return next((b.count for b in breakdown if b.label == label), 0)


async def _boolean_rate(db: AsyncSession, user_id: str, model, flag_column) -> RateMetric:
    total = (await db.execute(select(func.count()).select_from(model).where(model.user_id == user_id))).scalar_one()
    positive = (
        await db.execute(
            select(func.count()).select_from(model).where(model.user_id == user_id, flag_column.is_(True))
        )
    ).scalar_one()
    rate = round(positive / total * 100, 1) if total > 0 else None
    return RateMetric(total=total, positive=positive, rate_percentage=rate)


# ============================================================================
# Endpoints: métricas semanales
# ============================================================================
@router.get("/weekly", response_model=List[SearchMetricsWeekResponse])
async def get_weekly_search_metrics(
    limit: int = Query(12, ge=1, le=104, description="Number of most recent weeks to return"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Weekly job-search metrics for the authenticated user: applications sent,
    response rate, interviews scheduled, offers and rejections.
    """
    stmt = text(
        """
        SELECT week_start, applications_sent, responses_received,
               response_rate_percentage, interviews_scheduled, offers, rejections
        FROM search_metrics_view
        WHERE user_id = :user_id
        ORDER BY week_start DESC
        LIMIT :limit
        """
    )
    result = await db.execute(stmt, {"user_id": current_user.id, "limit": limit})
    rows = result.mappings().all()
    return [SearchMetricsWeekResponse(**row) for row in rows]


# ============================================================================
# Endpoints: panorama general de búsqueda
# ============================================================================
@router.get("/search-overview", response_model=SearchOverviewResponse)
async def get_search_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Aggregated snapshot across the 12 Operativa de Búsqueda tables, computed
    live per request (nothing here is stored): the funnel from vacantes to
    ofertas, breakdowns by evaluation/track/status/category, the fit-scoring
    rubric, market-segment performance, and the active search plan's progress.
    """
    user_id = current_user.id

    vacancies_total = (
        await db.execute(select(func.count()).select_from(Vacancy).where(Vacancy.user_id == user_id))
    ).scalar_one()
    applications_total = (
        await db.execute(select(func.count()).select_from(Application).where(Application.user_id == user_id))
    ).scalar_one()
    interviews_total = (
        await db.execute(select(func.count()).select_from(Interview).where(Interview.user_id == user_id))
    ).scalar_one()
    offers_total = (
        await db.execute(
            select(func.count())
            .select_from(Application)
            .where(Application.user_id == user_id, Application.current_status == "offer")
        )
    ).scalar_one()

    funnel = [
        FunnelStage(label="Vacantes", value=vacancies_total),
        FunnelStage(label="Aplicaciones", value=applications_total),
        FunnelStage(label="Entrevistas", value=interviews_total),
        FunnelStage(label="Ofertas", value=offers_total),
    ]

    vacancies_by_evaluation = await _count_by(db, user_id, Vacancy, Vacancy.evaluation)
    vacancies_by_track = await _count_by(db, user_id, Vacancy, Vacancy.track_category)

    fit_stats = (
        await db.execute(
            select(
                func.avg(Vacancy.fit_percentage),
                func.min(Vacancy.fit_percentage),
                func.max(Vacancy.fit_percentage),
            ).where(Vacancy.user_id == user_id)
        )
    ).one()
    fit_avg, fit_min, fit_max = fit_stats

    market_segments_rows = (
        await db.execute(
            select(MarketSegment)
            .where(MarketSegment.user_id == user_id, MarketSegment.is_active.is_(True))
            .order_by(MarketSegment.priority.desc())
        )
    ).scalars().all()
    market_segments = [
        MarketSegmentMetric(
            channel_name=m.channel_name,
            market_type=m.market_type,
            priority=m.priority,
            applications_made=m.applications_made or 0,
            responses_received=m.responses_received or 0,
            interviews_achieved=m.interviews_achieved or 0,
        )
        for m in market_segments_rows
    ]

    networking_by_status = await _count_by(db, user_id, NetworkingContact, NetworkingContact.contact_status)
    networking_by_category = await _count_by(db, user_id, NetworkingContact, NetworkingContact.role_category)

    companies_by_tier = await _count_by(db, user_id, TargetCompany, TargetCompany.tier)
    companies_by_status = await _count_by(db, user_id, TargetCompany, TargetCompany.status)

    fit_factor_rows = (
        await db.execute(
            select(FitScoringFactor)
            .where(FitScoringFactor.user_id == user_id)
            .order_by(FitScoringFactor.display_order.asc())
        )
    ).scalars().all()
    fit_scoring_factors = [
        FitFactorMetric(factor_name=f.factor_name, weight_percentage=f.weight_percentage) for f in fit_factor_rows
    ]

    active_plan_row = (
        await db.execute(
            select(SearchPlan)
            .where(SearchPlan.user_id == user_id, SearchPlan.plan_status == "in_progress")
            .order_by(SearchPlan.period_start.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    active_search_plan = (
        SearchPlanMetric(
            period_start=active_plan_row.period_start,
            period_end=active_plan_row.period_end,
            plan_status=active_plan_row.plan_status,
            completion_percentage=active_plan_row.completion_percentage or 0,
            target_cvs_sent=active_plan_row.target_cvs_sent or 0,
            target_interviews=active_plan_row.target_interviews or 0,
            target_offers=active_plan_row.target_offers or 0,
        )
        if active_plan_row
        else None
    )

    applications_by_status = await _count_by(db, user_id, Application, Application.current_status)
    interviews_by_result = await _count_by(db, user_id, Interview, Interview.interview_result)
    networking_activities_by_category = await _sum_by(
        db, user_id, NetworkingActivity, NetworkingActivity.category, NetworkingActivity.times_completed
    )
    application_interactions_response_rate = await _response_rate(
        db, user_id, ApplicationInteraction, ApplicationInteraction.response_received
    )
    contact_interactions_response_rate = await _response_rate(
        db, user_id, ContactInteraction, ContactInteraction.response_received
    )
    contact_interactions_opportunity_rate = await _boolean_rate(
        db, user_id, ContactInteraction, ContactInteraction.generated_opportunity
    )

    # Stage-to-stage conversion, not just the raw funnel counts above.
    funnel_conversion_rates = [
        _kpi("Vacantes → Aplicaciones", applications_total, vacancies_total),
        _kpi("Aplicaciones → Entrevistas", interviews_total, applications_total),
        _kpi("Entrevistas → Ofertas", offers_total, interviews_total),
        _kpi("Tasa de Éxito Total", offers_total, vacancies_total, f"{offers_total} ofertas de {vacancies_total} vacantes"),
    ]

    apply_count = _count_for_label(vacancies_by_evaluation, "apply")
    do_not_apply_count = _count_for_label(vacancies_by_evaluation, "do_not_apply")
    vacancy_kpis = [
        _kpi("Tasa de Fit", apply_count, apply_count + do_not_apply_count, f"{apply_count} de {apply_count + do_not_apply_count} evaluadas"),
        _kpi("Tasa de Aplicación sobre Fit", applications_total, apply_count, f"{applications_total} de {apply_count} con fit"),
    ]

    # Where vacancies actually come from, and which of those channels produce
    # results (not just volume) - `search_platform_id` when the vacancy is
    # linked to a tracked platform profile, else the free-text `source`.
    platform_label = func.coalesce(SearchPlatform.name, Vacancy.source, "Sin plataforma")
    platform_rows = (
        await db.execute(
            select(
                platform_label.label("platform"),
                func.count(func.distinct(Vacancy.id)),
                func.count(func.distinct(Application.id)),
                func.count(func.distinct(Interview.id)),
                func.count(func.distinct(case((Application.current_status == "offer", Application.id)))),
            )
            .select_from(Vacancy)
            .outerjoin(SearchPlatform, Vacancy.search_platform_id == SearchPlatform.id)
            .outerjoin(Application, Application.vacancy_id == Vacancy.id)
            .outerjoin(Interview, Interview.application_id == Application.id)
            .where(Vacancy.user_id == user_id)
            .group_by(platform_label)
            .order_by(func.count(func.distinct(Vacancy.id)).desc())
        )
    ).all()
    vacancies_by_platform = [
        PlatformResult(
            platform=platform,
            vacancies=vac_count,
            applications=app_count,
            interviews=ivw_count,
            offers=offer_count,
            application_rate_percentage=round(app_count / vac_count * 100, 1) if vac_count > 0 else None,
        )
        for platform, vac_count, app_count, ivw_count, offer_count in platform_rows
    ]

    converted_count = _count_for_label(networking_by_status, "converted")
    networking_total = sum(b.count for b in networking_by_status)
    networking_kpis = [
        _kpi("Tasa de Conversión de Contactos", converted_count, networking_total),
        _kpi(
            "Tasa de Respuesta",
            contact_interactions_response_rate.positive,
            contact_interactions_response_rate.total,
        ),
        _kpi(
            "Tasa de Oportunidad Generada",
            contact_interactions_opportunity_rate.positive,
            contact_interactions_opportunity_rate.total,
        ),
    ]

    return SearchOverviewResponse(
        funnel=funnel,
        vacancies_by_evaluation=vacancies_by_evaluation,
        vacancies_by_track=vacancies_by_track,
        fit_percentage_avg=round(float(fit_avg), 1) if fit_avg is not None else None,
        fit_percentage_min=fit_min,
        fit_percentage_max=fit_max,
        market_segments=market_segments,
        networking_by_status=networking_by_status,
        networking_by_category=networking_by_category,
        companies_by_tier=companies_by_tier,
        companies_by_status=companies_by_status,
        fit_scoring_factors=fit_scoring_factors,
        active_search_plan=active_search_plan,
        applications_by_status=applications_by_status,
        interviews_by_result=interviews_by_result,
        networking_activities_by_category=networking_activities_by_category,
        application_interactions_response_rate=application_interactions_response_rate,
        contact_interactions_response_rate=contact_interactions_response_rate,
        contact_interactions_opportunity_rate=contact_interactions_opportunity_rate,
        funnel_conversion_rates=funnel_conversion_rates,
        vacancy_kpis=vacancy_kpis,
        networking_kpis=networking_kpis,
        vacancies_by_platform=vacancies_by_platform,
    )
