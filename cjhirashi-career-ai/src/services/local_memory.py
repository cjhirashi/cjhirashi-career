"""
Memoria local — PG (historial) + Qdrant (hechos semánticos).

Memoria del agente — historial PG (corto plazo) + Qdrant (semántica).
"""
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.agent_system_conversations import AgentSystemConversation, AgentSystemConversationMessage
from services import qdrant_service
from services.bedrock.embeddings import embed_text
from services.bedrock.errors import BedrockError


# ============================================================================
# Memoria de conversación (PostgreSQL)
# ============================================================================

async def list_memory_events(
    db: AsyncSession, user_id: str, session_id: str, max_results: int = 50
) -> List[Dict[str, Any]]:
    """Mensajes PG de una conversación, formato compatible con la UI de memoria."""
    conv = await db.execute(
        select(AgentSystemConversation).where(
            AgentSystemConversation.user_id == user_id,
            AgentSystemConversation.session_id == session_id,
        )
    )
    conversation = conv.scalar_one_or_none()
    if not conversation:
        return []

    result = await db.execute(
        select(AgentSystemConversationMessage)
        .where(AgentSystemConversationMessage.conversation_id == conversation.id)
        .order_by(AgentSystemConversationMessage.created_at.asc())
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


# ============================================================================
# Búsqueda semántica (Qdrant)
# ============================================================================

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


# ============================================================================
# Memoria manual
# ============================================================================

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


_AGENT_NOTE_KEY = "agent-notes"


async def list_agent_notes(user_id: str, profile_id: str, limit: int = 40) -> List[Dict[str, Any]]:
    """Notas propias de un agente L1/L2 (Qdrant type=agent_note)."""
    rows = await qdrant_service.scroll_points(
        user_id=user_id,
        resource_type="agent_note",
        extra_must={"agent_profile_id": profile_id},
        limit=limit,
    )
    notes: List[Dict[str, Any]] = []
    for row in rows:
        notes.append(
            {
                "id": str(row.get("record_id") or ""),
                "text": row.get("text") or "",
            }
        )
    return [note for note in notes if note["id"] and note["text"]]


async def create_agent_note(user_id: str, profile_id: str, text: str) -> Dict[str, Any]:
    """Indexa una nota de memoria propia del perfil."""
    trimmed = text.strip()
    if not trimmed:
        raise BedrockError("El texto de memoria no puede estar vacío")
    record_id = str(int(hashlib.sha256(f"{profile_id}:{trimmed}".encode()).hexdigest()[:8], 16) % 2_000_000_000)
    vector = await embed_text(trimmed)
    await qdrant_service.upsert_point(
        user_id=user_id,
        resource_type="agent_note",
        resource_key=_AGENT_NOTE_KEY,
        record_id=record_id,
        text=trimmed,
        vector=vector,
        extra_payload={"agent_profile_id": profile_id},
    )
    return {"id": record_id, "text": trimmed}


async def delete_agent_note(record_id: str) -> None:
    await qdrant_service.delete_point(resource_key=_AGENT_NOTE_KEY, record_id=record_id)
