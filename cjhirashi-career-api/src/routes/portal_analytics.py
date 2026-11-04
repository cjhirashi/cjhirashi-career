"""
Portal analytics routers - D1 (read-only) and D2 (CRUD configuration).

D1: Read-only resources for portal-sites, portal-visitors, portal-visits,
    portal-events, portal-daily with filtering, sorting, pagination.

D2: CRUD resources for portal-goals, portal-funnels, portal-annotations.
"""
# ============================================================================
# Imports
# ============================================================================
from typing import List, Optional, Type, Any
import json
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import Date, select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database import Base, get_db
from middleware.auth import get_current_user
from models.user import User

# Models
from models.portal_site import PortalSite
from models.portal_visitor import PortalVisitor
from models.portal_visit import PortalVisit
from models.portal_event import PortalEvent
from models.portal_daily import PortalDaily
from models.portal_goal import PortalGoal
from models.portal_funnel import PortalFunnel
from models.portal_annotation import PortalAnnotation

# Schemas
from schemas.portal_analytics import (
    PortalSiteOut, PortalVisitorOut, PortalVisitOut, PortalEventOut, PortalDailyOut,
    PortalGoalCreate, PortalGoalUpdate, PortalGoalOut,
    PortalFunnelCreate, PortalFunnelUpdate, PortalFunnelOut,
    PortalAnnotationCreate, PortalAnnotationUpdate, PortalAnnotationOut,
)

from routes.career_common import build_crud_router


# ============================================================================
# D1: Read-only router factory
# ============================================================================

def build_portal_readonly_router(
    *,
    prefix: str,
    tags: List[str],
    model: Type[Base],
    response_schema: Type[BaseModel],
    time_column: str,
    entity_name: str,
) -> APIRouter:
    """
    Create a read-only APIRouter for portal analytics resources.

    Endpoints:
    - GET "" (list)
    - GET "/count"
    - GET "/{item_id}"

    No POST/PUT/DELETE. All endpoints require Depends(get_current_user) and
    filter by model.user_id == current_user.id (row-level security).

    Parameters:
    - skip (>=0): pagination offset
    - limit (1..200, default 50): page size
    - sort_by: column name; if invalid or omitted, sort by time_column desc then id desc
    - sort_dir (asc|desc, default desc)
    - since (str ISO): filter time_column >= since
    - until (str ISO): filter time_column < until (or < until+1 day for Date)
    - site_id: filter by site_id
    - filters (str JSON): {columna: valor | [valores]} for scalar columns only
    """
    router = APIRouter(prefix=prefix, tags=tags)

    class CountResponse(BaseModel):
        count: int

    def _parse_datetime(s: str) -> datetime:
        """Parse ISO datetime string or date."""
        try:
            dt = datetime.fromisoformat(s)
            # If only date provided (no time), assume midnight UTC
            if len(s) == 10:  # "YYYY-MM-DD"
                return dt.replace(hour=0, minute=0, second=0, microsecond=0)
            return dt
        except (ValueError, AttributeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid datetime format: {s!r}. Use ISO 8601.",
            )

    def _parse_filters(raw: Optional[str]) -> Optional[dict]:
        """Parse JSON filters; raise 400 if invalid."""
        if not raw or not raw.strip():
            return None
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="filters must be a JSON object",
            ) from exc
        if not isinstance(parsed, dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="filters must be a JSON object",
            )
        return parsed

    def _get_model_columns() -> set:
        """Return set of valid scalar column names for this model."""
        columns = set()
        for col in model.__table__.columns:
            # Skip JSONB and complex types
            if "JSONB" not in str(col.type):
                columns.add(col.name)
        return columns

    time_is_date = isinstance(model.__table__.columns[time_column].type, Date)

    def _time_range(since: Optional[str], until: Optional[str]) -> List[Any]:
        """Conditions for the time window; a Date column is compared by day, inclusive."""
        time_col = getattr(model, time_column)
        conds: List[Any] = []
        if since:
            since_val = _parse_datetime(since)
            conds.append(time_col >= (since_val.date() if time_is_date else since_val))
        if until:
            if time_is_date:
                conds.append(time_col <= _parse_datetime(until).date())
            elif len(until) == 10:
                conds.append(time_col < _parse_datetime(until) + timedelta(days=1))
            else:
                conds.append(time_col < _parse_datetime(until))
        return conds

    def _build_filters(filters_dict: dict) -> List[Any]:
        """
        Build SQLAlchemy filter conditions from parsed JSON.
        Validates that columns exist and are scalar.
        """
        if not filters_dict:
            return []

        valid_cols = _get_model_columns()
        conditions = []

        for col_name, value in filters_dict.items():
            if col_name not in valid_cols:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Column {col_name!r} does not exist or is not scalar",
                )
            col = getattr(model, col_name)
            if isinstance(value, list):
                # IN operator
                conditions.append(col.in_(value))
            else:
                # Equality
                conditions.append(col == value)

        return conditions

    @router.get("", response_model=List[response_schema], summary=f"List {entity_name}")
    async def list_items(
        skip: int = Query(0, ge=0),
        limit: int = Query(50, ge=1, le=200),
        sort_by: Optional[str] = Query(None),
        sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
        since: Optional[str] = Query(None),
        until: Optional[str] = Query(None),
        site_id: Optional[str] = Query(None),
        filters: Optional[str] = Query(None),
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        # Base query: only this user's rows
        stmt = select(model).where(model.user_id == current_user.id)

        # Add site_id filter if provided
        if site_id:
            stmt = stmt.where(model.site_id == site_id)

        for cond in _time_range(since, until):
            stmt = stmt.where(cond)

        filters_dict = _parse_filters(filters)
        if filters_dict:
            filter_conditions = _build_filters(filters_dict)
            for cond in filter_conditions:
                stmt = stmt.where(cond)

        order_col = getattr(model, time_column)
        if sort_by:
            if sort_by not in model.__table__.columns:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Column {sort_by!r} does not exist",
                )
            order_col = getattr(model, sort_by)

        # Default sort: by time_column desc, then id desc
        if sort_dir == "desc":
            stmt = stmt.order_by(order_col.desc())
        else:
            stmt = stmt.order_by(order_col.asc())

        # Secondary sort by id for stable pagination
        if sort_by and sort_by != "id":
            if sort_dir == "desc":
                stmt = stmt.order_by(getattr(model, "id").desc())
            else:
                stmt = stmt.order_by(getattr(model, "id").asc())

        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    @router.get("/count", response_model=CountResponse, summary=f"Count {entity_name}")
    async def count_items(
        since: Optional[str] = Query(None),
        until: Optional[str] = Query(None),
        site_id: Optional[str] = Query(None),
        filters: Optional[str] = Query(None),
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        stmt = select(func.count()).select_from(model).where(model.user_id == current_user.id)

        if site_id:
            stmt = stmt.where(model.site_id == site_id)

        for cond in _time_range(since, until):
            stmt = stmt.where(cond)

        filters_dict = _parse_filters(filters)
        if filters_dict:
            filter_conditions = _build_filters(filters_dict)
            for cond in filter_conditions:
                stmt = stmt.where(cond)

        result = await db.execute(stmt)
        count = result.scalar()
        return CountResponse(count=count or 0)

    @router.get("/{item_id}", response_model=response_schema, summary=f"Get a single {entity_name}")
    async def get_item(
        item_id: str,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        stmt = select(model).where(
            and_(model.id == item_id, model.user_id == current_user.id)
        )
        result = await db.execute(stmt)
        obj = result.scalar_one_or_none()
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{entity_name} not found",
            )
        return obj

    return router


# ============================================================================
# D2: CRUD configuration resources
# ============================================================================

def build_portal_config_routers() -> List[APIRouter]:
    """
    Build and return CRUD routers for portal configuration resources:
    - portal-goals
    - portal-funnels
    - portal-annotations

    All use build_crud_router with vectorize=False (not indexed).
    """
    routers = []

    # PortalGoal
    routers.append(build_crud_router(
        prefix="/portal-goals",
        tags=["Portal Analytics - Config"],
        model=PortalGoal,
        create_schema=PortalGoalCreate,
        update_schema=PortalGoalUpdate,
        response_schema=PortalGoalOut,
        entity_name="portal goal",
        vectorize=False,
    ))

    # PortalFunnel
    routers.append(build_crud_router(
        prefix="/portal-funnels",
        tags=["Portal Analytics - Config"],
        model=PortalFunnel,
        create_schema=PortalFunnelCreate,
        update_schema=PortalFunnelUpdate,
        response_schema=PortalFunnelOut,
        entity_name="portal funnel",
        vectorize=False,
    ))

    # PortalAnnotation
    routers.append(build_crud_router(
        prefix="/portal-annotations",
        tags=["Portal Analytics - Config"],
        model=PortalAnnotation,
        create_schema=PortalAnnotationCreate,
        update_schema=PortalAnnotationUpdate,
        response_schema=PortalAnnotationOut,
        entity_name="portal annotation",
        vectorize=False,
    ))

    return routers


# ============================================================================
# Create main router with D1 read-only endpoints
# ============================================================================

router = APIRouter(prefix="/career", tags=["Portal Analytics"])

# D1: Read-only resources
router.include_router(build_portal_readonly_router(
    prefix="/portal-sites",
    tags=["Portal Analytics - Read-only"],
    model=PortalSite,
    response_schema=PortalSiteOut,
    time_column="created_at",
    entity_name="portal site",
))

router.include_router(build_portal_readonly_router(
    prefix="/portal-visitors",
    tags=["Portal Analytics - Read-only"],
    model=PortalVisitor,
    response_schema=PortalVisitorOut,
    time_column="last_seen",
    entity_name="portal visitor",
))

router.include_router(build_portal_readonly_router(
    prefix="/portal-visits",
    tags=["Portal Analytics - Read-only"],
    model=PortalVisit,
    response_schema=PortalVisitOut,
    time_column="started_at",
    entity_name="portal visit",
))

router.include_router(build_portal_readonly_router(
    prefix="/portal-events",
    tags=["Portal Analytics - Read-only"],
    model=PortalEvent,
    response_schema=PortalEventOut,
    time_column="created_at",
    entity_name="portal event",
))

router.include_router(build_portal_readonly_router(
    prefix="/portal-daily",
    tags=["Portal Analytics - Read-only"],
    model=PortalDaily,
    response_schema=PortalDailyOut,
    time_column="day",
    entity_name="portal daily",
))

# D2: Configuration CRUD resources
for config_router in build_portal_config_routers():
    router.include_router(config_router)
