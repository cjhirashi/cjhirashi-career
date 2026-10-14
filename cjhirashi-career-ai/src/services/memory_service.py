"""
Servicio de memoria del agente (RF-022, D-29, D-30): notas, memoria manual, hechos y eventos.

Traslado de `local_memory` de la API sin Qdrant ni embeddings: la búsqueda es full-text en Postgres
(`memory_repo`) y los eventos salen de los mensajes de la conversación. Guardar dos veces la misma
nota/memoria manual no duplica: la clave determinista `source_ref` (`memory_source_ref`, compartida
con la migración desde Qdrant) apoya la unicidad `user_id + source_ref`.
"""
import hashlib
from typing import Any, Dict, List, Optional

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models.bedrock_agent_memory import BedrockAgentMemory
from models.bedrock_conversation import BedrockConversation, BedrockConversationMessage
from repositories import memory_repo

MAX_LIMIT = 50
_SOURCE = "harness"


class MemoryServiceError(ValueError):
    """Entrada de memoria inválida (texto vacío)."""


def _clean(text: Optional[str]) -> str:
    return (text or "").replace("\x00", "").strip()


def _bound(n: int) -> int:
    return max(1, min(MAX_LIMIT, int(n)))


def memory_source_ref(kind: str, text: str, profile_id: Optional[str] = None) -> str:
    """Clave de deduplicación (D-30): `note:<profile_id>:<h>` | `manual:<h>`, `h` = sha256[:40] del texto limpio."""
    digest = hashlib.sha256(_clean(text).encode()).hexdigest()[:40]
    if kind == "manual":
        return f"manual:{digest}"
    if kind == "note":
        if not profile_id:
            raise ValueError("kind='note' requiere profile_id")
        return f"note:{profile_id}:{digest}"
    raise ValueError(f"kind no soportado: {kind!r}")


async def _find_by_ref(db: AsyncSession, user_id: str, source_ref: str) -> Optional[BedrockAgentMemory]:
    result = await db.execute(
        select(BedrockAgentMemory).where(
            BedrockAgentMemory.user_id == user_id, BedrockAgentMemory.source_ref == source_ref
        )
    )
    return result.scalar_one_or_none()


async def _create_idempotent(
    db: AsyncSession, user_id: str, kind: str, text: str, profile_id: Optional[str]
) -> Dict[str, str]:
    source_ref = memory_source_ref(kind, text, profile_id)
    row = await _find_by_ref(db, user_id, source_ref)
    if row is None:
        try:
            row = await memory_repo.add_memory(
                db, user_id, kind, text, agent_profile_id=profile_id, source=_SOURCE, source_ref=source_ref
            )
        except IntegrityError:
            await db.rollback()
            row = await _find_by_ref(db, user_id, source_ref)
            if row is None:
                raise
    return {"id": row.id, "text": row.text}


async def list_memory_events(
    db: AsyncSession, user_id: str, session_id: str, max_results: int = 50
) -> List[Dict[str, Any]]:
    """Mensajes de una conversación propia (los más antiguos, en orden cronológico), forma de la API."""
    conv = (
        await db.execute(
            select(BedrockConversation).where(
                BedrockConversation.user_id == user_id, BedrockConversation.session_id == session_id
            )
        )
    ).scalar_one_or_none()
    if not conv:
        return []
    result = await db.execute(
        select(BedrockConversationMessage)
        .where(BedrockConversationMessage.conversation_id == conv.id)
        .order_by(BedrockConversationMessage.created_at.asc())
        .limit(_bound(max_results))
    )
    return [
        {
            "eventId": str(m.id),
            "eventTimestamp": m.created_at.isoformat() if m.created_at else None,
            "payload": [{"conversational": {"role": m.role.upper(), "content": {"text": m.content}}}],
        }
        for m in result.scalars().all()
    ]


async def retrieve_memory_records(
    db: AsyncSession, user_id: str, query: str, top_k: int = 10
) -> List[Dict[str, Any]]:
    """Búsqueda full-text sobre la memoria del usuario (mejor primero)."""
    hits = await memory_repo.search_memory(db, user_id, _clean(query), limit=_bound(top_k))
    return [
        {
            "memoryRecordId": row.id,
            "content": {"text": row.text},
            "score": score,
            "namespaces": [row.kind, row.agent_profile_id or "global"],
            "createdAt": row.created_at.isoformat(),
        }
        for row, score in hits
    ]


async def create_manual_memory(db: AsyncSession, user_id: str, text: str) -> Dict[str, str]:
    """Memoria manual global del usuario; idempotente por texto."""
    trimmed = _clean(text)
    if not trimmed:
        raise MemoryServiceError("El texto de memoria no puede estar vacío")
    return await _create_idempotent(db, user_id, "manual", trimmed, None)


async def list_agent_notes(db: AsyncSession, user_id: str, profile_id: str, limit: int = 40) -> List[Dict[str, str]]:
    """Notas (`kind='note'`) propias del perfil, las más recientes primero."""
    result = await db.execute(
        select(BedrockAgentMemory)
        .where(
            BedrockAgentMemory.user_id == user_id,
            BedrockAgentMemory.kind == "note",
            BedrockAgentMemory.agent_profile_id == profile_id,
        )
        .order_by(BedrockAgentMemory.created_at.desc(), BedrockAgentMemory.id.desc())
        .limit(_bound(limit))
    )
    return [{"id": r.id, "text": r.text} for r in result.scalars().all()]


async def create_agent_note(db: AsyncSession, user_id: str, profile_id: str, text: str) -> Dict[str, str]:
    """Nota propia del perfil; idempotente por (usuario, perfil, texto)."""
    trimmed = _clean(text)
    if not trimmed:
        raise MemoryServiceError("El texto de memoria no puede estar vacío")
    return await _create_idempotent(db, user_id, "note", trimmed, profile_id)


async def delete_agent_note(db: AsyncSession, user_id: str, note_id: str) -> bool:
    """Borra una nota propia (`kind='note'`); `False` si no existe, es de otro usuario o no es una nota."""
    result = await db.execute(
        delete(BedrockAgentMemory).where(
            BedrockAgentMemory.id == note_id,
            BedrockAgentMemory.user_id == user_id,
            BedrockAgentMemory.kind == "note",
        )
    )
    await db.commit()
    return result.rowcount > 0
