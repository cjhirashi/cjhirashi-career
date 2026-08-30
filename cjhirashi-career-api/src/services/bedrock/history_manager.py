"""
Historial de conversación en PostgreSQL — ventana deslizante para Converse.

PG es la fuente de verdad del historial de chat. Ver ADR-008.
"""
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.agent_system_conversations import AgentSystemConversation, AgentSystemConversationMessage
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
) -> AgentSystemConversation:
    result = await db.execute(
        select(AgentSystemConversation).where(
            AgentSystemConversation.user_id == user_id,
            AgentSystemConversation.session_id == session_id,
        )
    )
    row = result.scalar_one_or_none()
    if row:
        if agent_profile_id and not row.agent_profile_id:
            row.agent_profile_id = agent_profile_id
            await db.commit()
        return row
    row = AgentSystemConversation(
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


async def append_message(db: AsyncSession, conversation: AgentSystemConversation, role: str, content: str) -> None:
    db.add(AgentSystemConversationMessage(conversation_id=conversation.id, role=role, content=content))
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
        select(AgentSystemConversation).where(
            AgentSystemConversation.user_id == user_id,
            AgentSystemConversation.session_id == session_id,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        return []
    msgs = await db.execute(
        select(AgentSystemConversationMessage)
        .where(AgentSystemConversationMessage.conversation_id == conv.id)
        .order_by(AgentSystemConversationMessage.created_at.asc())
    )
    rows = msgs.scalars().all()
    if window and len(rows) > window:
        rows = rows[-window:]
    out: List[Dict[str, Any]] = []
    for m in rows:
        content = sanitize_assistant_reply(m.content) if m.role == "assistant" else m.content
        # Bedrock Converse rechaza bloques de texto vacíos ("text content blocks
        # must be non-empty"). Filas persistidas antes de este guard, o filas con
        # contenido en blanco, se reemplazan por un placeholder para no romper el
        # siguiente turno.
        out.append({"role": m.role, "content": [{"text": content or "(sin texto)"}]})
    return out


# ============================================================================
# Listado de conversaciones
# ============================================================================

async def list_conversations(
    db: AsyncSession,
    user_id: str,
    session_type: Optional[str] = None,
    agent_profile_id: Optional[str] = None,
) -> List[AgentSystemConversation]:
    q = select(AgentSystemConversation).where(AgentSystemConversation.user_id == user_id)
    if session_type:
        q = q.where(AgentSystemConversation.session_type == session_type)
    if agent_profile_id:
        q = q.where(AgentSystemConversation.agent_profile_id == agent_profile_id)
    q = q.order_by(AgentSystemConversation.updated_at.desc())
    result = await db.execute(q)
    return list(result.scalars().all())
