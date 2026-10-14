"""
Servicio de uso: coste estimado, registro best-effort, presupuesto diario y métricas.

Traslado de `usage_logger.py`, `budget.py` y del handler `/usage-metrics` (API). El coste y
el ahorro de caché salen del `ModelProvider` (la tabla de precios vive tras la frontera del proveedor).
El registro nunca rompe el chat; el presupuesto se pasa como parámetro (lo resuelve
quien llama desde los ajustes en ejecución).
"""
import logging
from typing import Any, Awaitable, Callable, Dict, Optional

from providers.base import ProviderError, Usage
from repositories import usage_repo

logger = logging.getLogger(__name__)


def _provider():
    from config import get_provider

    return get_provider()


def cache_read_savings_usd(model_id: str, cache_read_tokens: int) -> float:
    """Ahorro por servir tokens desde caché en vez de a precio normal, derivado solo de `estimate_cost`
    (el protocolo no expone la tabla de precios): coste como entrada normal menos coste como lectura de caché."""
    provider = _provider()
    return provider.estimate_cost(model_id, Usage(input_tokens=cache_read_tokens)) - provider.estimate_cost(
        model_id, Usage(cache_read_tokens=cache_read_tokens)
    )


class BudgetExceeded(ProviderError):
    """Presupuesto diario de inferencia agotado."""


# Alias de paridad con el nombre de la API (`services/bedrock/errors.py`).
BedrockBudgetExceeded = BudgetExceeded


def _default_session_factory():
    from database import AsyncSessionLocal

    return AsyncSessionLocal()


async def record_turn_usage(
    user_id: str,
    session_id: str,
    model_id: str,
    usage: Usage,
    *,
    session_factory: Optional[Callable[[], Any]] = None,
) -> None:
    """Una fila por turno completo. Best-effort: un fallo se registra y no se propaga."""
    try:
        factory = session_factory or _default_session_factory
        async with factory() as db:
            await usage_repo.add_turn_log(
                db,
                user_id=user_id,
                session_id=session_id,
                model_id=model_id,
                input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens,
                cache_read_tokens=usage.cache_read_tokens,
                cache_write_tokens=usage.cache_write_tokens,
                estimated_cost_usd=_provider().estimate_cost(model_id, usage),
            )
    except Exception:
        logger.exception("Failed to record turn usage")


async def record_round_log(
    *,
    user_id: str,
    session_id: str,
    model_id: Optional[str],
    round_type: str,
    usage: Optional[Usage] = None,
    tool_name: Optional[str] = None,
    agent_profile_id: Optional[str] = None,
    notes: Optional[str] = None,
    fixed_cost_usd: Optional[float] = None,
    session_factory: Optional[Callable[[], Any]] = None,
) -> None:
    """Granular: cada llamada Converse, delegación o imagen. Best-effort."""
    try:
        usage = usage or Usage()
        if fixed_cost_usd is not None:
            cost = fixed_cost_usd
        else:
            cost = _provider().estimate_cost(model_id, usage) if model_id else 0.0
        factory = session_factory or _default_session_factory
        async with factory() as db:
            await usage_repo.add_round_log(
                db,
                user_id=user_id,
                session_id=session_id,
                model_id=model_id,
                round_type=round_type,
                tool_name=tool_name,
                agent_profile_id=agent_profile_id,
                input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens,
                cache_read_tokens=usage.cache_read_tokens,
                cache_write_tokens=usage.cache_write_tokens,
                estimated_cost_usd=cost,
                notes=notes,
            )
    except Exception:
        logger.exception("Failed to record round log")


async def get_daily_spend_usd(db, user_id: str) -> float:
    return await usage_repo.get_daily_spend_usd(db, user_id)


async def assert_budget_available(db, user_id: str, daily_budget: float) -> None:
    """Lanza `BudgetExceeded` si el gasto del día >= presupuesto."""
    spent = await get_daily_spend_usd(db, user_id)
    if spent >= daily_budget:
        raise BudgetExceeded(
            f"Presupuesto diario agotado (${spent:.2f} / ${daily_budget:.2f}). "
            "Ajusta BEDROCK_DAILY_BUDGET_USD o espera mañana."
        )


async def get_remaining_budget_usd(db, user_id: str, daily_budget: float) -> float:
    return max(0.0, daily_budget - await get_daily_spend_usd(db, user_id))


async def get_usage_metrics(db, user_id: str, *, days: int, daily_budget: float) -> Dict[str, Any]:
    by_model = await usage_repo.usage_by_model(db, user_id)
    by_day = await usage_repo.usage_by_day(db, user_id, days)
    spent = await get_daily_spend_usd(db, user_id)
    return {
        "by_model": by_model,
        "by_day": by_day,
        "total_estimated_cost_usd": sum(m["estimated_cost_usd"] for m in by_model),
        "total_cache_read_tokens": sum(m["cache_read_tokens"] for m in by_model),
        "total_cache_savings_usd": sum(
            cache_read_savings_usd(m["model_id"], m["cache_read_tokens"]) for m in by_model
        ),
        "daily_budget_usd": daily_budget,
        "daily_spent_usd": spent,
        "daily_remaining_usd": max(0.0, daily_budget - spent),
    }
