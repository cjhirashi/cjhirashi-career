"""
Repositorio de uso del asistente: `bedrock_usage_logs` (una fila por turno) y
`bedrock_usage_round_logs` (una fila por llamada Converse, tool o imagen).

Traslado de `usage_logger.py`, `budget.py` y del handler `/usage-metrics` de la API.
La fuente del gasto diario y de las métricas es `bedrock_usage_logs`: sumar además las
rondas duplicaría el conteo (ADR-019).
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.bedrock_usage_log import BedrockUsageLog
from models.bedrock_usage_round_log import BedrockUsageRoundLog


async def add_turn_log(
    db: AsyncSession,
    *,
    user_id: str,
    session_id: str,
    model_id: str,
    input_tokens: int,
    output_tokens: int,
    cache_read_tokens: int,
    cache_write_tokens: int,
    estimated_cost_usd: float,
    created_at: Optional[datetime] = None,
) -> None:
    row = BedrockUsageLog(
        user_id=user_id,
        session_id=session_id,
        model_id=model_id,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_read_tokens=cache_read_tokens,
        cache_write_tokens=cache_write_tokens,
        estimated_cost_usd=estimated_cost_usd,
    )
    if created_at is not None:
        row.created_at = created_at
    db.add(row)
    await db.commit()


async def add_round_log(
    db: AsyncSession,
    *,
    user_id: str,
    session_id: str,
    model_id: Optional[str],
    round_type: str,
    tool_name: Optional[str],
    agent_profile_id: Optional[str],
    input_tokens: int,
    output_tokens: int,
    cache_read_tokens: int,
    cache_write_tokens: int,
    estimated_cost_usd: float,
    notes: Optional[str],
) -> None:
    db.add(
        BedrockUsageRoundLog(
            user_id=user_id,
            session_id=session_id,
            model_id=model_id,
            round_type=round_type,
            tool_name=tool_name,
            agent_profile_id=agent_profile_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_tokens=cache_read_tokens,
            cache_write_tokens=cache_write_tokens,
            estimated_cost_usd=estimated_cost_usd,
            notes=notes,
        )
    )
    await db.commit()


async def sum_cost_since(db: AsyncSession, user_id: str, since: datetime) -> float:
    result = await db.execute(
        select(func.coalesce(func.sum(BedrockUsageLog.estimated_cost_usd), 0)).where(
            BedrockUsageLog.user_id == user_id,
            BedrockUsageLog.created_at >= since,
        )
    )
    return float(result.scalar_one() or 0)


async def get_daily_spend_usd(db: AsyncSession, user_id: str) -> float:
    """Gasto estimado desde las 00:00 UTC de hoy, desde `bedrock_usage_logs`."""
    today = datetime.now(timezone.utc).date()
    day_start = datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc)
    return await sum_cost_since(db, user_id, day_start)


async def usage_by_model(db: AsyncSession, user_id: str) -> List[Dict[str, Any]]:
    stmt = (
        select(
            BedrockUsageLog.model_id,
            func.sum(BedrockUsageLog.input_tokens),
            func.sum(BedrockUsageLog.output_tokens),
            func.sum(BedrockUsageLog.cache_read_tokens),
            func.sum(BedrockUsageLog.cache_write_tokens),
            func.sum(BedrockUsageLog.estimated_cost_usd),
            func.count(),
        )
        .where(BedrockUsageLog.user_id == user_id)
        .group_by(BedrockUsageLog.model_id)
        .order_by(func.sum(BedrockUsageLog.estimated_cost_usd).desc())
    )
    rows = (await db.execute(stmt)).all()
    return [
        {
            "model_id": model_id,
            "input_tokens": int(inp or 0),
            "output_tokens": int(out or 0),
            "cache_read_tokens": int(cache_read or 0),
            "cache_write_tokens": int(cache_write or 0),
            "estimated_cost_usd": float(cost or 0),
            "turns": turns,
        }
        for model_id, inp, out, cache_read, cache_write, cost, turns in rows
    ]


async def usage_by_day(db: AsyncSession, user_id: str, days: int) -> List[Dict[str, Any]]:
    day_col = func.date(BedrockUsageLog.created_at)
    stmt = (
        select(
            day_col,
            func.sum(BedrockUsageLog.input_tokens),
            func.sum(BedrockUsageLog.output_tokens),
            func.sum(BedrockUsageLog.cache_read_tokens),
            func.sum(BedrockUsageLog.cache_write_tokens),
            func.sum(BedrockUsageLog.estimated_cost_usd),
        )
        .where(
            BedrockUsageLog.user_id == user_id,
            BedrockUsageLog.created_at >= func.now() - func.make_interval(0, 0, 0, days),
        )
        .group_by(day_col)
        .order_by(day_col.asc())
    )
    rows = (await db.execute(stmt)).all()
    return [
        {
            "day": day,
            "input_tokens": int(inp or 0),
            "output_tokens": int(out or 0),
            "cache_read_tokens": int(cache_read or 0),
            "cache_write_tokens": int(cache_write or 0),
            "estimated_cost_usd": float(cost or 0),
        }
        for day, inp, out, cache_read, cache_write, cost in rows
    ]
