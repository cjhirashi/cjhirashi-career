"""
Memoria del agente — historial de conversación en PostgreSQL.
"""
from typing import Any, Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.bedrock_conversation import BedrockConversation, BedrockConversationMessage


# ============================================================================
# Memoria de conversación (PostgreSQL)
# ============================================================================

async def list_memory_events(
    db: AsyncSession, user_id: str, session_id: str, max_results: int = 50
) -> List[Dict[str, Any]]:
    """Mensajes PG de una conversación, formato compatible con la UI de memoria."""
    conv = await db.execute(
        select(BedrockConversation).where(
            BedrockConversation.user_id == user_id,
            BedrockConversation.session_id == session_id,
        )
    )
    conversation = conv.scalar_one_or_none()
    if not conversation:
        return []

    result = await db.execute(
        select(BedrockConversationMessage)
        .where(BedrockConversationMessage.conversation_id == conversation.id)
        .order_by(BedrockConversationMessage.created_at.asc())
        .limit(max_results)
    )
    messages = result.scalars().all()
    events: List[Dict[str, Any]] = []
    for msg in messages:
        events.append(
            {
                "eventId": str(msg.id),
                "eventTimestamp": msg.created_at.isoformat() if msg.created_at else None,
                "payload": [
                    {
                        "conversational": {
                            "role": msg.role.upper(),
                            "content": {"text": msg.content},
                        }
                    }
                ],
            }
        )
    return events
