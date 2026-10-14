"""
Repositorio de conversaciones y mensajes (`bedrock_conversations`, `bedrock_conversation_messages`).

Traslado de `history_manager.py` y de las funciones de conversación de `bedrock_service.py`
de la API. `user_id` es un texto opaco (sin FK a `users`): el aislamiento por usuario se
hace en cada consulta.
"""
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.bedrock_conversation import BedrockConversation, BedrockConversationMessage
from providers.reply_text import sanitize_assistant_reply

_TITLE_MAX_CHARS = 60
_TITLE_COLUMN_MAX = 255


def conversation_title_from(text: str) -> str:
    clean = " ".join(text.split())
    return (clean[:_TITLE_MAX_CHARS] + "…") if len(clean) > _TITLE_MAX_CHARS else clean or "Nueva conversación"


async def _find(db: AsyncSession, user_id: str, session_id: str) -> Optional[BedrockConversation]:
    result = await db.execute(
        select(BedrockConversation).where(
            BedrockConversation.user_id == user_id,
            BedrockConversation.session_id == session_id,
        )
    )
    return result.scalar_one_or_none()


async def get_or_create_conversation(
    db: AsyncSession,
    user_id: str,
    session_id: str,
    first_message: str,
    session_type: str = "contextual",
    agent_profile_id: Optional[str] = None,
) -> BedrockConversation:
    row = await _find(db, user_id, session_id)
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


async def append_message(db: AsyncSession, conversation_id: str, role: str, content: str) -> None:
    """Recibe el id ya resuelto (no el objeto ORM): un `rollback()` de una tool fallida en el mismo
    turno expira el objeto y tocar un atributo expirado revienta con MissingGreenlet."""
    db.add(BedrockConversationMessage(conversation_id=conversation_id, role=role, content=content))
    await db.commit()


async def load_converse_messages(
    db: AsyncSession, user_id: str, session_id: str, window: int
) -> List[Dict[str, Any]]:
    """Últimos `window` mensajes user/assistant como historial Converse (solo texto); `0` = todos."""
    conv = await _find(db, user_id, session_id)
    if not conv:
        return []
    msgs = await db.execute(
        select(BedrockConversationMessage)
        .where(BedrockConversationMessage.conversation_id == conv.id)
        .order_by(BedrockConversationMessage.created_at.asc(), BedrockConversationMessage.id.asc())
    )
    rows = msgs.scalars().all()
    if window and len(rows) > window:
        rows = rows[-window:]
    out: List[Dict[str, Any]] = []
    for m in rows:
        content = sanitize_assistant_reply(m.content) if m.role == "assistant" else m.content
        # Converse rechaza bloques de texto vacíos: se sustituyen por un placeholder.
        out.append({"role": m.role, "content": [{"text": content or "(sin texto)"}]})
    return out


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
    result = await db.execute(q.order_by(BedrockConversation.updated_at.desc()))
    return list(result.scalars().all())


async def get_conversation_messages(
    db: AsyncSession, user_id: str, session_id: str
) -> List[BedrockConversationMessage]:
    result = await db.execute(
        select(BedrockConversation)
        .options(selectinload(BedrockConversation.messages))
        .where(BedrockConversation.session_id == session_id, BedrockConversation.user_id == user_id)
    )
    conversation = result.scalar_one_or_none()
    return list(conversation.messages) if conversation else []


async def rename_conversation(db: AsyncSession, user_id: str, session_id: str, title: str) -> bool:
    conversation = await _find(db, user_id, session_id)
    if conversation is None:
        return False
    conversation.title = title[:_TITLE_COLUMN_MAX]
    await db.commit()
    return True


async def delete_conversation(db: AsyncSession, user_id: str, session_id: str) -> bool:
    conversation = await _find(db, user_id, session_id)
    if conversation is None:
        return False
    await db.delete(conversation)
    await db.commit()
    return True


async def conversation_counts_by_profile(db: AsyncSession, user_id: str) -> Dict[str, int]:
    """Nº de conversaciones del usuario por `agent_profile_id` (las que no tienen perfil no cuentan)."""
    result = await db.execute(
        select(BedrockConversation.agent_profile_id, func.count())
        .where(BedrockConversation.user_id == user_id)
        .group_by(BedrockConversation.agent_profile_id)
    )
    return {pid: int(total) for pid, total in result.all() if pid}
