"""
Registro de uso — turnos (bedrock_usage_logs) y rounds granulares.

Best-effort: nunca falla el chat si el log falla.
"""
import logging
from typing import Dict, Optional

from config import settings
from database import AsyncSessionLocal
from models.agent_system_usage_logs import AgentSystemUsageLog
from models.agent_system_usage_round_logs import AgentSystemUsageRoundLog
from services.error_reporting import report_error

logger = logging.getLogger(__name__)


# ============================================================================
# Estimación de costo
# ============================================================================

# Ratios estándar de prompt caching (Anthropic / Bedrock), relativos al precio
# de entrada normal del modelo: la lectura de caché cuesta 0.10x y la escritura
# 1.25x. OJO: 1.25x asume TTL de 5 min, que es lo que emite
# converse_client._cache_point() ({"type": "default"}). Si algún día se usa
# {"ttl": "1h"}, la escritura pasa a 2.0x y hay que parametrizar este ratio.
_CACHE_READ_RATIO = 0.10
_CACHE_WRITE_RATIO = 1.25


def _estimate_cost(
    model_id: str,
    input_tokens: int,
    output_tokens: int,
    cache_read_tokens: int = 0,
    cache_write_tokens: int = 0,
) -> float:
    pricing = settings.BEDROCK_AVAILABLE_MODELS.get(model_id, {})
    price_in = pricing.get("price_input_per_million", 0) / 1_000_000
    price_out = pricing.get("price_output_per_million", 0) / 1_000_000
    return (
        input_tokens * price_in
        + output_tokens * price_out
        + cache_read_tokens * price_in * _CACHE_READ_RATIO
        + cache_write_tokens * price_in * _CACHE_WRITE_RATIO
    )


def _cache_tokens(usage: Optional[Dict[str, int]]) -> tuple[int, int]:
    """(cache_read, cache_write) desde el dict de usage del cliente Converse."""
    if not usage:
        return 0, 0
    return (
        usage.get("cacheReadInputTokens", 0) or 0,
        usage.get("cacheWriteInputTokens", 0) or 0,
    )


def cache_read_savings_usd(model_id: str, cache_read_tokens: int) -> float:
    """Ahorro estimado por servir esos tokens desde caché (0.10x) en vez de a
    precio de entrada normal (1.0x). Para el panel de costos."""
    price_in = settings.BEDROCK_AVAILABLE_MODELS.get(model_id, {}).get(
        "price_input_per_million", 0
    ) / 1_000_000
    return cache_read_tokens * price_in * (1 - _CACHE_READ_RATIO)


# ============================================================================
# Registro por turno completo
# ============================================================================

async def record_turn_usage(
    user_id: str,
    session_id: str,
    model_id: str,
    usage: Dict[str, int],
) -> None:
    """Una fila por turno completo (compatibilidad panel costos actual)."""
    try:
        cache_read, cache_write = _cache_tokens(usage)
        async with AsyncSessionLocal() as db:
            db.add(
                AgentSystemUsageLog(
                    user_id=user_id,
                    session_id=session_id,
                    model_id=model_id,
                    input_tokens=usage.get("inputTokens", 0),
                    output_tokens=usage.get("outputTokens", 0),
                    cache_read_tokens=cache_read,
                    cache_write_tokens=cache_write,
                    estimated_cost_usd=_estimate_cost(
                        model_id,
                        usage.get("inputTokens", 0),
                        usage.get("outputTokens", 0),
                        cache_read,
                        cache_write,
                    ),
                )
            )
            await db.commit()
    except Exception as exc:
        logger.exception("Failed to record turn usage")
        report_error(
            str(exc) or "Failed to record turn usage", "bedrock:usage_logger.turn",
            error_type=type(exc).__name__, exc=exc, severity="warning",
        )


# ============================================================================
# Registro granular por round
# ============================================================================

async def record_round_log(
    *,
    user_id: str,
    session_id: str,
    model_id: Optional[str],
    round_type: str,
    usage: Optional[Dict[str, int]] = None,
    tool_name: Optional[str] = None,
    agent_profile_id: Optional[str] = None,
    notes: Optional[str] = None,
    fixed_cost_usd: Optional[float] = None,
) -> None:
    """Granular: cada Converse call, delegación o generate_image."""
    try:
        inp = usage.get("inputTokens", 0) if usage else 0
        out = usage.get("outputTokens", 0) if usage else 0
        cache_read, cache_write = _cache_tokens(usage)
        cost = fixed_cost_usd if fixed_cost_usd is not None else (
            _estimate_cost(model_id or "", inp, out, cache_read, cache_write) if model_id else 0.0
        )
        async with AsyncSessionLocal() as db:
            db.add(
                AgentSystemUsageRoundLog(
                    user_id=user_id,
                    session_id=session_id,
                    model_id=model_id,
                    round_type=round_type,
                    tool_name=tool_name,
                    agent_profile_id=agent_profile_id,
                    input_tokens=inp,
                    output_tokens=out,
                    cache_read_tokens=cache_read,
                    cache_write_tokens=cache_write,
                    estimated_cost_usd=cost,
                    notes=notes,
                )
            )
            await db.commit()
    except Exception as exc:
        logger.exception("Failed to record round log")
        report_error(
            str(exc) or "Failed to record round log", "bedrock:usage_logger.round",
            error_type=type(exc).__name__, exc=exc, severity="warning",
        )
