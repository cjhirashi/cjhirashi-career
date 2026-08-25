"""Alcance de una metodología operativa a uno o más agentes."""
from typing import Any, Optional

from services.bedrock.agent_profiles import AGENT_METHODOLOGIES


def applies_to_agent(agent_profile_ids: Optional[Any], caller_profile_id: Optional[str]) -> bool:
    """True si la metodología es visible para el agente caller.

    Lista vacía o null = todos. El guardián L2 `agent_methodologies` ve todas.
    """
    if not caller_profile_id or caller_profile_id == AGENT_METHODOLOGIES:
        return True
    ids = agent_profile_ids or []
    if not isinstance(ids, list) or not ids:
        return True
    return caller_profile_id in ids
