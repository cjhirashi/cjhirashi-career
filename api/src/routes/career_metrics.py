"""
Career domain (v2) - Metrics.

Read-only endpoint over `search_metrics_view`, a SQL view computed from
`applications` and `interviews` (never captured/edited by hand). No
SQLAlchemy ORM model is mapped for the view (Postgres views have no
primary key), so it is queried directly with parametrized SQL, still
scoped to the authenticated user.
"""
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from middleware.auth import get_current_user
from models.user import User
from schemas.career_metrics import SearchMetricsWeekResponse

router = APIRouter(prefix="/career/metrics", tags=["Career - Metrics"])


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
