"""
Memoria local — PG (historial) + Qdrant (hechos semánticos).

Reemplaza AgentCore Memory cuando BEDROCK_USE_LOCAL_HARNESS=true.
"""
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.bedrock_conversation import BedrockConversation, BedrockConversationMessage
from services import qdrant_service
from services.bedrock.embeddings import embed_text
from services.bedrock.errors import BedrockError


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


async def retrieve_memory_records(user_id: str, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
    """Búsqueda semántica Qdrant — hechos de carrera + memoria manual."""
    vector = await embed_text(query)
    hits = await qdrant_service.search(user_id=user_id, vector=vector, top_k=top_k)
    records: List[Dict[str, Any]] = []
    for hit in hits:
        records.append(
            {
                "memoryRecordId": f"{hit.get('resource_key')}:{hit.get('record_id')}",
                "content": {"text": hit.get("text", "")},
                "score": hit.get("score"),
                "namespaces": [hit.get("type"), hit.get("resource_key")],
            }
        )
    return records


async def create_manual_memory(user_id: str, text: str) -> None:
    """Indexa un hecho manual en Qdrant (disponible de inmediato en búsqueda)."""
    trimmed = text.strip()
    if not trimmed:
        raise BedrockError("El texto de memoria no puede estar vacío")

    record_id = int(hashlib.sha256(trimmed.encode()).hexdigest()[:8], 16) % 2_000_000_000
    vector = await embed_text(trimmed)
    await qdrant_service.upsert_point(
        user_id=user_id,
        resource_type="manual_memory",
        resource_key="manual_memory",
        record_id=record_id,
        text=trimmed,
        vector=vector,
    )
