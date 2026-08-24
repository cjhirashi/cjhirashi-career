"""
Delegación — sub-turno de especialista invocado por orquestador.

Ver docs/BEDROCK-SYSTEM.md § chat general.
"""
from typing import Any, AsyncIterator, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from services.bedrock.agent_profiles import AgentProfile, get_profile


async def run_specialist_sub_turn(
    db: AsyncSession,
    *,
    user_id: int,
    session_id: str,
    profile: AgentProfile,
    task: str,
    context: Optional[str],
) -> Dict[str, Any]:
    """Ejecuta un sub-turno acotado (sin delegación anidada) y devuelve resumen."""
    from services.bedrock.agent_loop import run_single_turn_sync

    message = task
    if context:
        message = f"{task}\n\nContexto:\n{context}"
    result = await run_single_turn_sync(
        db,
        user_id=user_id,
        session_id=session_id,
        message=message,
        chat_surface="contextual",
        agent_profile_id=profile.id,
        page_context=None,
        model_id=profile.default_model_id,
        max_round_trips=2,
        record_history=False,
    )
    return {"summary": result.get("reply", ""), "affected_resources": result.get("affected_resources", [])}
