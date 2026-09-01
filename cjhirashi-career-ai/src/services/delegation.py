"""
delegation.py — Sub-turno hacia un especialista de nivel inferior.

L1 y L2 invocan esto; L3 nunca delega. El sub-turno no escribe historial de
sesión (el agente user-facing lo hace al final) y puede anidar L2→L3.

Ver ADR-012.
"""
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from services.bedrock.agent_profiles import AgentProfile


async def run_specialist_sub_turn(
    db: AsyncSession,
    *,
    user_id: str,
    session_id: str,
    profile: AgentProfile,
    task: str,
    context: Optional[str],
    delegation_depth: int = 0,
) -> Dict[str, Any]:
    """
    Ejecuta un sub-turno delegado a un agente de nivel inferior.

    No persiste mensajes en la conversación del usuario. L2 puede a su vez
    delegar a L3 (el loop valida nivel y profundidad).
    """
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
        max_round_trips=4,
        record_history=False,
        load_session_history=False,
        delegation_depth=delegation_depth + 1,
    )

    return {
        "summary": result.get("reply", ""),
        "affected_resources": result.get("affected_resources", []),
    }
