"""
Registro de uso — turnos (bedrock_usage_logs) y rounds granulares.

Best-effort: nunca falla el chat si el log falla.
"""
import logging
from typing import Dict, Optional

from config import settings
from database import AsyncSessionLocal
from models.bedrock_usage_log import BedrockUsageLog
from models.bedrock_usage_round_log import BedrockUsageRoundLog

logger = logging.getLogger(__name__)


def _estimate_cost(model_id: str, input_tokens: int, output_tokens: int) -> float:
    pricing = settings.BEDROCK_AVAILABLE_MODELS.get(model_id, {})
    return (
        input_tokens * pricing.get("price_input_per_million", 0) / 1_000_000
        + output_tokens * pricing.get("price_output_per_million", 0) / 1_000_000
    )


async def record_turn_usage(
    user_id: int,
    session_id: str,
    model_id: str,
    usage: Dict[str, int],
) -> None:
    """Una fila por turno completo (compatibilidad panel costos actual)."""
    try:
        async with AsyncSessionLocal() as db:
            db.add(
                BedrockUsageLog(
                    user_id=user_id,
                    session_id=session_id,
                    model_id=model_id,
                    input_tokens=usage.get("inputTokens", 0),
                    output_tokens=usage.get("outputTokens", 0),
                    estimated_cost_usd=_estimate_cost(
                        model_id, usage.get("inputTokens", 0), usage.get("outputTokens", 0)
                    ),
                )
            )
            await db.commit()
    except Exception:
        logger.exception("Failed to record turn usage")


async def record_round_log(
    *,
    user_id: int,
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
        cost = fixed_cost_usd if fixed_cost_usd is not None else (
            _estimate_cost(model_id or "", inp, out) if model_id else 0.0
        )
        async with AsyncSessionLocal() as db:
            db.add(
                BedrockUsageRoundLog(
                    user_id=user_id,
                    session_id=session_id,
                    model_id=model_id,
                    round_type=round_type,
                    tool_name=tool_name,
                    agent_profile_id=agent_profile_id,
                    input_tokens=inp,
                    output_tokens=out,
                    estimated_cost_usd=cost,
                    notes=notes,
                )
            )
            await db.commit()
    except Exception:
        logger.exception("Failed to record round log")
