"""
Presupuesto diario USD — bloqueo de inferencia cuando se agota.

Fuente única: `bedrock_usage_logs` (una fila por turno, ya sumada sobre sus
rondas). `bedrock_usage_round_logs` es el mismo gasto desglosado por ronda —
sumarlo además duplicaría el conteo (ver ADR-019). El panel `/usage-metrics`
usa la misma tabla, así que "gasto hoy" y "total" son coherentes.
"""
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.agent_system_usage_logs import AgentSystemUsageLog
from services.errors import BedrockBudgetExceeded


# ============================================================================
# Consulta de gasto diario
# ============================================================================

async def get_daily_spend_usd(db: AsyncSession, user_id: str) -> float:
    """Gasto estimado hoy (UTC), desde bedrock_usage_logs (una fila por turno)."""
    today = datetime.now(timezone.utc).date()
    day_start = datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc)

    result = await db.execute(
        select(func.coalesce(func.sum(AgentSystemUsageLog.estimated_cost_usd), 0)).where(
            AgentSystemUsageLog.user_id == user_id,
            AgentSystemUsageLog.created_at >= day_start,
        )
    )
    return float(result.scalar_one() or 0)


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
