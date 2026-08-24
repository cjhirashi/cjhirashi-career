"""
Historial de conversación en PostgreSQL — ventana deslizante para Converse.

PG es la fuente de verdad (no AgentCore Memory). Ver ADR-008.
"""
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.bedrock_conversation import BedrockConversation, BedrockConversationMessage


def conversation_title_from(text: str) -> str:
    clean = " ".join(text.split())
    return (clean[:60] + "…") if len(clean) > 60 else clean or "Nueva conversación"


async def get_or_create_conversation(
    db: AsyncSession,
    user_id: int,
    session_id: str,
    first_message: str,
    session_type: str = "contextual",
) -> BedrockConversation:
    result = await db.execute(
        select(BedrockConversation).where(
            BedrockConversation.user_id == user_id,
            BedrockConversation.session_id == session_id,
        )
    )
    row = result.scalar_one_or_none()
    if row:
        return row
    row = BedrockConversation(
        user_id=user_id,
        session_id=session_id,
        title=conversation_title_from(first_message),
        session_type=session_type,
    )
    db.add(row)
    await db.flush()
    await db.refresh(row)
    await db.commit()
    return row


async def append_message(db: AsyncSession, conversation: BedrockConversation, role: str, content: str) -> None:
    db.add(BedrockConversationMessage(conversation_id=conversation.id, role=role, content=content))
    await db.commit()


async def load_converse_messages(
    db: AsyncSession,
    user_id: int,
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
        out.append({"role": m.role, "content": [{"text": m.content}]})
    return out


async def list_conversations(
    db: AsyncSession, user_id: int, session_type: Optional[str] = None
) -> List[BedrockConversation]:
    q = select(BedrockConversation).where(BedrockConversation.user_id == user_id)
    if session_type:
        q = q.where(BedrockConversation.session_type == session_type)
    q = q.order_by(BedrockConversation.updated_at.desc())
    result = await db.execute(q)
    return list(result.scalars().all())
