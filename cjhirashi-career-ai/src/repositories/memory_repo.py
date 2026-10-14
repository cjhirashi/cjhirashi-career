"""
Repositorio de la memoria del agente: `bedrock_agent_memory` con búsqueda full-text (RF-022).

Sustituye a la memoria que vivía solo en Qdrant (D-15). La búsqueda usa la columna generada
`search_vector` (índice GIN) y `websearch_to_tsquery` con `settings.MEMORY_FTS_CONFIG`
(`spanish_unaccent` por defecto, D-24/D-29: stemming en español e ignora tildes).
`user_id` es un texto opaco: el aislamiento por usuario se hace en cada consulta.
"""
from typing import List, Optional, Tuple

from sqlalchemy import cast, delete, func, or_, select
from sqlalchemy.dialects.postgresql import REGCONFIG
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models.bedrock_agent_memory import BedrockAgentMemory


def _profile_filter(agent_profile_id: Optional[str]):
    """Con perfil: las del perfil + las globales (NULL) del usuario. Sin perfil: sin filtro extra."""
    if agent_profile_id is None:
        return None
    return or_(
        BedrockAgentMemory.agent_profile_id == agent_profile_id,
        BedrockAgentMemory.agent_profile_id.is_(None),
    )


async def add_memory(
    db: AsyncSession,
    user_id: str,
    kind: str,
    text: str,
    *,
    agent_profile_id: Optional[str] = None,
    source: str = "harness",
    source_ref: Optional[str] = None,
) -> BedrockAgentMemory:
    """Inserta una memoria. `IntegrityError` se propaga si `(user_id, source_ref)` ya existe."""
    row = BedrockAgentMemory(
        user_id=user_id,
        kind=kind,
        text=text,
        agent_profile_id=agent_profile_id,
        source=source,
        source_ref=source_ref,
    )
    db.add(row)
    # flush + refresh: asigna el id `bam-N` y trae `search_vector` (columna generada).
    await db.flush()
    await db.refresh(row)
    await db.commit()
    return row


async def list_memory(
    db: AsyncSession,
    user_id: str,
    *,
    agent_profile_id: Optional[str] = None,
    kind: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[BedrockAgentMemory]:
    """Memorias del usuario, las más recientes primero."""
    stmt = select(BedrockAgentMemory).where(BedrockAgentMemory.user_id == user_id)
    profile = _profile_filter(agent_profile_id)
    if profile is not None:
        stmt = stmt.where(profile)
    if kind is not None:
        stmt = stmt.where(BedrockAgentMemory.kind == kind)
    stmt = (
        stmt.order_by(BedrockAgentMemory.created_at.desc(), BedrockAgentMemory.id.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def delete_memory(db: AsyncSession, user_id: str, memory_id: str) -> bool:
    """Borra una memoria propia. `False` si no existe o es de otro usuario."""
    result = await db.execute(
        delete(BedrockAgentMemory).where(
            BedrockAgentMemory.id == memory_id,
            BedrockAgentMemory.user_id == user_id,
        )
    )
    await db.commit()
    return result.rowcount > 0


async def search_memory(
    db: AsyncSession,
    user_id: str,
    query: str,
    *,
    agent_profile_id: Optional[str] = None,
    limit: int = 10,
) -> List[Tuple[BedrockAgentMemory, float]]:
    """Búsqueda full-text ordenada por `ts_rank` descendente.

    La consulta del usuario viaja siempre como parámetro ligado (nunca concatenada en SQL);
    `websearch_to_tsquery` tolera sintaxis arbitraria. Consulta vacía -> `[]`.
    """
    if not query or not query.strip():
        return []
    config = cast(settings.MEMORY_FTS_CONFIG, REGCONFIG)  # valor ya validado [a-z_]+ y ligado
    tsquery = func.websearch_to_tsquery(config, query)
    rank = func.ts_rank(BedrockAgentMemory.search_vector, tsquery).label("rank")
    stmt = select(BedrockAgentMemory, rank).where(
        BedrockAgentMemory.user_id == user_id,
        BedrockAgentMemory.search_vector.op("@@")(tsquery),
    )
    profile = _profile_filter(agent_profile_id)
    if profile is not None:
        stmt = stmt.where(profile)
    stmt = stmt.order_by(rank.desc(), BedrockAgentMemory.id.desc()).limit(limit)
    result = await db.execute(stmt)
    return [(row, float(score)) for row, score in result.all()]
