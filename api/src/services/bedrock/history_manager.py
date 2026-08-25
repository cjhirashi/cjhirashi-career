"""
Historial de conversación en PostgreSQL — ventana deslizante para Converse.

PG es la fuente de verdad del historial de chat. Ver ADR-008.
"""
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.bedrock_conversation import BedrockConversation, BedrockConversationMessage
from services.bedrock.reply_text import sanitize_assistant_reply


# ============================================================================
# Utilidades de conversación
# ============================================================================

def conversation_title_from(text: str) -> str:
    clean = " ".join(text.split())
    return (clean[:60] + "…") if len(clean) > 60 else clean or "Nueva conversación"


# ============================================================================
# Persistencia de mensajes
# ============================================================================

async def get_or_create_conversation(
    db: AsyncSession,
    user_id: str,
    session_id: str,
    first_message: str,
    session_type: str = "contextual",
    agent_profile_id: Optional[str] = None,
) -> BedrockConversation:
    result = await db.execute(
        select(BedrockConversation).where(
            BedrockConversation.user_id == user_id,
            BedrockConversation.session_id == session_id,
        )
    )
    row = result.scalar_one_or_none()
    if row:
        if agent_profile_id and not row.agent_profile_id:
            row.agent_profile_id = agent_profile_id
            await db.commit()
        return row
    row = BedrockConversation(
        user_id=user_id,
        session_id=session_id,
        title=conversation_title_from(first_message),
        session_type=session_type,
        agent_profile_id=agent_profile_id,
    )
    db.add(row)
    await db.flush()
    await db.refresh(row)
    await db.commit()
    return row


async def append_message(db: AsyncSession, conversation: BedrockConversation, role: str, content: str) -> None:
    db.add(BedrockConversationMessage(conversation_id=conversation.id, role=role, content=content))
    await db.commit()


# ============================================================================
# Carga de historial Converse
# ============================================================================

async def load_converse_messages(
    db: AsyncSession,
    user_id: str,
    session_id: str,
    window: int,
) -> List[Dict[str, Any]]:
    """Últimos N mensajes user/assistant como historial Converse (solo texto)."""
    result = await db.execute(
        select(BedrockConversation).where(
            BedrockConversation.user_id == user_id,
            BedrockConversation.session_id == session_id,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        return []
    msgs = await db.execute(
        select(BedrockConversationMessage)
        .where(BedrockConversationMessage.conversation_id == conv.id)
        .order_by(BedrockConversationMessage.created_at.asc())
    )
    rows = msgs.scalars().all()
    if window and len(rows) > window:
        rows = rows[-window:]
    out: List[Dict[str, Any]] = []
    for m in rows:
        content = sanitize_assistant_reply(m.content) if m.role == "assistant" else m.content
        out.append({"role": m.role, "content": [{"text": content}]})
    return out


# ============================================================================
# Listado de conversaciones
# ============================================================================

async def list_conversations(
    db: AsyncSession,
    user_id: str,
    session_type: Optional[str] = None,
    agent_profile_id: Optional[str] = None,
) -> List[BedrockConversation]:
    q = select(BedrockConversation).where(BedrockConversation.user_id == user_id)
    if session_type:
        q = q.where(BedrockConversation.session_type == session_type)
    if agent_profile_id:
        q = q.where(BedrockConversation.agent_profile_id == agent_profile_id)
    q = q.order_by(BedrockConversation.updated_at.desc())
    result = await db.execute(q)
    return list(result.scalars().all())
