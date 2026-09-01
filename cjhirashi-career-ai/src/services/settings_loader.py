"""
Lectura de bedrock_settings — modelo activo y límites runtime.
"""
from dataclasses import dataclass
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models.agent_system_settings import AgentSystemSettings


# ============================================================================
# Configuración runtime del harness
# ============================================================================

@dataclass
class HarnessRuntimeSettings:
    active_model_id: str
    orchestrator_model_id: str
    max_round_trips: int
    history_window: int
    daily_budget_usd: float


# ============================================================================
# Lectura de settings desde PG
# ============================================================================

async def get_runtime_settings(db: AsyncSession) -> HarnessRuntimeSettings:
    result = await db.execute(select(AgentSystemSettings).limit(1))
    row = result.scalar_one_or_none()
    return HarnessRuntimeSettings(
        active_model_id=(row.active_model_id if row and row.active_model_id else settings.BEDROCK_DEFAULT_MODEL_ID),
        orchestrator_model_id=(
            row.orchestrator_model_id if row and row.orchestrator_model_id else settings.BEDROCK_ORCHESTRATOR_MODEL_ID
        ),
        max_round_trips=row.max_round_trips if row else settings.BEDROCK_MAX_ROUND_TRIPS,
        history_window=row.history_window if row else settings.BEDROCK_HISTORY_WINDOW,
        daily_budget_usd=float(row.daily_budget_usd if row else settings.BEDROCK_DAILY_BUDGET_USD),
    )


# ============================================================================
# Modelo activo
# ============================================================================

async def get_active_model_id(db: AsyncSession) -> str:
    return (await get_runtime_settings(db)).active_model_id


async def set_active_model_id(db: AsyncSession, model_id: str) -> None:
    result = await db.execute(select(AgentSystemSettings).limit(1))
    row = result.scalar_one_or_none()
    if row is None:
        row = AgentSystemSettings(active_model_id=model_id)
        db.add(row)
    else:
        row.active_model_id = model_id
    await db.commit()
