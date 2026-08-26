"""
Presupuesto diario USD — bloqueo de inferencia cuando se agota.

Suma bedrock_usage_logs + bedrock_usage_round_logs del día UTC.
"""
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models.bedrock_usage_log import BedrockUsageLog
from models.bedrock_usage_round_log import BedrockUsageRoundLog
from services.bedrock.errors import BedrockBudgetExceeded


# ============================================================================
# Consulta de gasto diario
# ============================================================================

async def get_daily_spend_usd(db: AsyncSession, user_id: str) -> float:
    """Gasto estimado hoy (logs por turno + round logs)."""
    today = datetime.now(timezone.utc).date()
    day_start = datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc)

    q1 = await db.execute(
        select(func.coalesce(func.sum(BedrockUsageLog.estimated_cost_usd), 0)).where(
            BedrockUsageLog.user_id == user_id,
            BedrockUsageLog.created_at >= day_start,
        )
    )
    q2 = await db.execute(
        select(func.coalesce(func.sum(BedrockUsageRoundLog.estimated_cost_usd), 0)).where(
            BedrockUsageRoundLog.user_id == user_id,
            BedrockUsageRoundLog.created_at >= day_start,
        )
    )
    total = float(q1.scalar_one() or 0) + float(q2.scalar_one() or 0)
    return total


# ============================================================================
# Validación de presupuesto
# ============================================================================

async def assert_budget_available(db: AsyncSession, user_id: str, daily_budget: float) -> None:
    """Lanza BedrockBudgetExceeded si el gasto del día >= presupuesto."""
    spent = await get_daily_spend_usd(db, user_id)
    if spent >= daily_budget:
        raise BedrockBudgetExceeded(
            f"Presupuesto diario agotado (${spent:.2f} / ${daily_budget:.2f}). "
            "Ajusta BEDROCK_DAILY_BUDGET_USD o espera mañana."
        )


# ============================================================================
# Presupuesto restante
# ============================================================================

async def get_remaining_budget_usd(db: AsyncSession, user_id: str, daily_budget: float) -> float:
    spent = await get_daily_spend_usd(db, user_id)
    return max(0.0, daily_budget - spent)
