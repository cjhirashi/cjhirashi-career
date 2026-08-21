"""
Agent Bedrock - chat, model switching, and usage-cost metrics.

No auth of its own: `get_current_user` is the exact same dependency every
other authenticated route in this API uses. Bedrock never gets a distinct
authorization scope - it operates with whatever the calling Admin Panel
session already has (see docs/01-INTRODUCTION.md, Security Model).
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db
from middleware.auth import get_current_user
from models.bedrock_usage_log import BedrockUsageLog
from models.user import User
from schemas.bedrock import (
    BedrockChatRequest,
    BedrockChatResponse,
    BedrockModelOption,
    BedrockModelStatusResponse,
    BedrockModelSwitchRequest,
    BedrockUsageByDay,
    BedrockUsageByModel,
    BedrockUsageMetricsResponse,
)
from services import bedrock_service
from services.bedrock_service import BedrockError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bedrock", tags=["Bedrock"])

# AgentCore Harness requires runtimeSessionId to be at least 33 characters.
_MIN_SESSION_ID_LENGTH = 33


def _require_configured() -> None:
    if not settings.AWS_ACCESS_KEY_ID or not settings.BEDROCK_HARNESS_ARN:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent Bedrock is not configured (missing AWS_ACCESS_KEY_ID/BEDROCK_HARNESS_ARN)",
        )


@router.post("/chat", response_model=BedrockChatResponse, summary="Chat with Agent Bedrock")
async def chat(
    payload: BedrockChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require_configured()
    if len(payload.session_id) < _MIN_SESSION_ID_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"session_id must be at least {_MIN_SESSION_ID_LENGTH} characters",
        )

    try:
        result = await bedrock_service.chat(db, current_user.id, payload.session_id, payload.message)
    except BedrockError as e:
        logger.error("Bedrock chat failed: %s", e)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    return BedrockChatResponse(**result)


@router.get("/model", response_model=BedrockModelStatusResponse, summary="Get the active chat model and the switchable allow-list")
async def get_model(current_user: User = Depends(get_current_user)):
    _require_configured()
    try:
        current_model_id = await bedrock_service.get_current_model()
    except BedrockError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    available = [
        BedrockModelOption(model_id=model_id, **info)
        for model_id, info in settings.BEDROCK_AVAILABLE_MODELS.items()
    ]
    return BedrockModelStatusResponse(current_model_id=current_model_id, available_models=available)


@router.post("/model", response_model=BedrockModelStatusResponse, summary="Switch the chat model")
async def switch_model(
    payload: BedrockModelSwitchRequest,
    current_user: User = Depends(get_current_user),
):
    _require_configured()
    if payload.model_id not in settings.BEDROCK_AVAILABLE_MODELS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown model_id: {payload.model_id}",
        )

    try:
        await bedrock_service.switch_model(payload.model_id)
    except BedrockError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    available = [
        BedrockModelOption(model_id=model_id, **info)
        for model_id, info in settings.BEDROCK_AVAILABLE_MODELS.items()
    ]
    return BedrockModelStatusResponse(current_model_id=payload.model_id, available_models=available)


@router.get("/usage-metrics", response_model=BedrockUsageMetricsResponse, summary="Token usage and estimated cost of the chat assistant")
async def get_usage_metrics(
    days: int = Query(30, ge=1, le=365, description="How many most-recent days to include"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = current_user.id

    by_model_stmt = (
        select(
            BedrockUsageLog.model_id,
            func.sum(BedrockUsageLog.input_tokens),
            func.sum(BedrockUsageLog.output_tokens),
            func.sum(BedrockUsageLog.estimated_cost_usd),
            func.count(),
        )
        .where(BedrockUsageLog.user_id == user_id)
        .group_by(BedrockUsageLog.model_id)
        .order_by(func.sum(BedrockUsageLog.estimated_cost_usd).desc())
    )
    by_model_rows = (await db.execute(by_model_stmt)).all()
    by_model = [
        BedrockUsageByModel(
            model_id=model_id,
            input_tokens=int(input_tokens or 0),
            output_tokens=int(output_tokens or 0),
            estimated_cost_usd=float(cost or 0),
            turns=turns,
        )
        for model_id, input_tokens, output_tokens, cost, turns in by_model_rows
    ]

    day_col = func.date(BedrockUsageLog.created_at)
    by_day_stmt = (
        select(
            day_col,
            func.sum(BedrockUsageLog.input_tokens),
            func.sum(BedrockUsageLog.output_tokens),
            func.sum(BedrockUsageLog.estimated_cost_usd),
        )
        .where(
            BedrockUsageLog.user_id == user_id,
            BedrockUsageLog.created_at >= func.now() - func.make_interval(0, 0, 0, days),
        )
        .group_by(day_col)
        .order_by(day_col.asc())
    )
    by_day_rows = (await db.execute(by_day_stmt)).all()
    by_day = [
        BedrockUsageByDay(
            day=day,
            input_tokens=int(input_tokens or 0),
            output_tokens=int(output_tokens or 0),
            estimated_cost_usd=float(cost or 0),
        )
        for day, input_tokens, output_tokens, cost in by_day_rows
    ]

    total_cost = sum(m.estimated_cost_usd for m in by_model)

    return BedrockUsageMetricsResponse(by_model=by_model, by_day=by_day, total_estimated_cost_usd=total_cost)
