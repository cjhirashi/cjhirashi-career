"""
Wrapper for bedrock_service - provides compatibility layer.

In FASE 3, this routes to local services.
In FASE 4+, this will route to orchestrator_client for cross-service calls.
"""

from typing import Any, AsyncIterator, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession


# Local service imports
from services import (
    agent_loop,
    budget,
    delegation,
    history_manager,
    local_memory,
    profile_catalog,
    profile_delegation,
    profile_photos,
    profile_prompts,
    tool_results,
    tools,
    usage_logger,
)


# Stub implementations - these should eventually call orchestrator_client


async def chat_stream(
    db: AsyncSession,
    user_id: str,
    session_id: str,
    message: str,
    turn_request: Optional[Any] = None,
) -> AsyncIterator:
    """Stream chat events from agent loop."""
    # TODO: Implement via orchestrator_client
    async for event in agent_loop.chat_stream(
        db, user_id, session_id, message, turn_request=turn_request
    ):
        yield event


async def get_current_model() -> str:
    """Get current model ID."""
    # TODO: Get from orchestrator_client
    return "claude-3-5-sonnet-20241022"


async def switch_model(model_id: str) -> None:
    """Switch to a different model."""
    # TODO: Call orchestrator_client
    pass


async def get_system_prompt(db: AsyncSession) -> str:
    """Get system prompt."""
    # TODO: Get from orchestrator_client
    return profile_prompts.get_default_system_prompt()


async def set_system_prompt(db: AsyncSession, text: str) -> None:
    """Set system prompt."""
    # TODO: Save to orchestrator_client
    pass


def default_system_prompt() -> str:
    """Get default system prompt."""
    return profile_prompts.get_default_system_prompt()


async def get_global_rules(db: AsyncSession) -> str:
    """Get global rules."""
    # TODO: Get from orchestrator_client
    return ""


async def set_global_rules(db: AsyncSession, text: str) -> None:
    """Set global rules."""
    # TODO: Save to orchestrator_client
    pass


def default_global_rules() -> str:
    """Get default global rules."""
    return ""


async def list_custom_tools(db: AsyncSession) -> List[Dict]:
    """List custom tools."""
    # TODO: Call orchestrator_client
    return []


async def create_custom_tool(db: AsyncSession, name: str, url: str, headers: Dict) -> Dict:
    """Create custom tool."""
    # TODO: Call orchestrator_client
    return {"id": "tmp", "name": name, "url": url}


async def set_custom_tool_enabled(db: AsyncSession, tool_id: str, is_enabled: bool) -> Dict:
    """Enable/disable custom tool."""
    # TODO: Call orchestrator_client
    return {"id": tool_id, "enabled": is_enabled}


async def delete_custom_tool(db: AsyncSession, tool_id: str) -> bool:
    """Delete custom tool."""
    # TODO: Call orchestrator_client
    return True


async def get_conversation_messages(db: AsyncSession, user_id: str, session_id: str) -> List[Dict]:
    """Get conversation messages."""
    # TODO: Call orchestrator_client
    return await history_manager.list_messages(db, session_id)


async def rename_conversation(db: AsyncSession, user_id: str, session_id: str, title: str) -> bool:
    """Rename conversation."""
    # TODO: Call orchestrator_client
    return True


async def delete_conversation(db: AsyncSession, user_id: str, session_id: str) -> bool:
    """Delete conversation."""
    # TODO: Call orchestrator_client
    return True


async def list_audit_log(db: AsyncSession, user_id: str, limit: int, offset: int) -> List[Dict]:
    """List audit log."""
    # TODO: Call orchestrator_client
    return []


async def restore_audit_entry(db: AsyncSession, user_id: str, audit_id: str) -> Optional[Dict]:
    """Restore audit entry."""
    # TODO: Call orchestrator_client
    return None


# Additional functions needed by services
def _get_repository(resource_key: str):
    """Get repository for a resource key."""
    # TODO: Return appropriate repository
    return None


async def _execute_tool(db: AsyncSession, user_id: str, tool_name: str, params: Dict) -> Dict:
    """Execute a tool."""
    # TODO: Call orchestrator_client
    return {}
