"""
Qdrant service - Agent Bedrock's local knowledge base.

Single collection (`settings.QDRANT_COLLECTION`), one point per record from
any of the ~30 career-domain tables (including `operational_methodologies`),
keyed by a deterministic id derived from `{resource_key}:{record_id}` so
upserts/deletes are idempotent - callers never need to track Qdrant's own
point ids. Every point carries a `user_id` payload field for row-level
isolation, mirroring every SQL table in this project (see
`repositories/career_repository.py`, which calls this module after every
create/update/delete).

Kept deliberately dependency-free of the rest of the app (no FastAPI, no
SQLAlchemy) - just talks to Qdrant. Callers are responsible for treating
failures as best-effort (log and continue) rather than fatal, since a stale
search index should never block a real database write.
"""
import uuid
from typing import Any, Dict, List, Optional

from qdrant_client import AsyncQdrantClient, models

from config import settings

_client: Optional[AsyncQdrantClient] = None


# ============================================================================
# Operaciones de colección
# ============================================================================

def _get_client() -> AsyncQdrantClient:
    global _client
    if _client is None:
        _client = AsyncQdrantClient(url=settings.QDRANT_URL)
    return _client


def _point_id(resource_key: str, record_id: str) -> str:
    """Qdrant point ids must be a UUID or an unsigned int - derive a stable
    UUID from the natural key so re-indexing the same record is an upsert,
    never a duplicate."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"career_knowledge:{resource_key}:{record_id}"))


async def _collection_exists() -> bool:
    client = _get_client()
    collections = await client.get_collections()
    return any(c.name == settings.QDRANT_COLLECTION for c in collections.collections)


async def _ensure_collection(vector_size: int) -> None:
    if await _collection_exists():
        return
    client = _get_client()
    await client.create_collection(
        collection_name=settings.QDRANT_COLLECTION,
        vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
    )


# ============================================================================
# Indexación
# ============================================================================

async def upsert_point(
    *,
    user_id: str,
    resource_type: str,
    resource_key: str,
    record_id: str,
    text: str,
    vector: List[float],
) -> None:
    """Index (or re-index) one record. `resource_type` is `"methodology"` or
    `"career_record"` - `operational_methodologies` goes through the same
    generic path as every other resource, since it's just another table
    behind `CareerRepository`."""
    await _ensure_collection(len(vector))
    client = _get_client()
    await client.upsert(
        collection_name=settings.QDRANT_COLLECTION,
        points=[
            models.PointStruct(
                id=_point_id(resource_key, record_id),
                vector=vector,
                payload={
                    "user_id": user_id,
                    "type": resource_type,
                    "resource_key": resource_key,
                    "record_id": record_id,
                    "text": text,
                },
            )
        ],
    )


async def delete_point(*, resource_key: str, record_id: str) -> None:
    client = _get_client()
    await client.delete(
        collection_name=settings.QDRANT_COLLECTION,
        points_selector=models.PointIdsList(points=[_point_id(resource_key, record_id)]),
    )


# ============================================================================
# Búsqueda
# ============================================================================

async def search(
    *,
    user_id: str,
    vector: List[float],
    top_k: int = 5,
    resource_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Semantic search scoped to `user_id`, optionally filtered to
    `"methodology"` or `"career_record"`. Returns `[]` if nothing has been
    indexed yet rather than erroring - an empty knowledge base is a valid
    state, not a failure."""
    if not await _collection_exists():
        return []
    client = _get_client()
    must = [models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id))]
    if resource_type:
        must.append(models.FieldCondition(key="type", match=models.MatchValue(value=resource_type)))
    result = await client.query_points(
        collection_name=settings.QDRANT_COLLECTION,
        query=vector,
        query_filter=models.Filter(must=must),
        limit=top_k,
    )
    return [{"score": point.score, **point.payload} for point in result.points]
