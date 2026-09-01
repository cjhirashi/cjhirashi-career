"""
Redis client singleton for caching, queues, and rate limiting.

FASE 1 (Queues/Caching): Redis Streams + consumer groups
- Prefix `queue:*` for message queues (linkedin:scheduled-posts, bedrock:scheduled-tasks)
- Prefix `cache:*` for application cache

FASE 5 (Rate Limiting): Centralized rate limiting via token bucket
FASE 7 (Observability): Distributed tracing via OpenTelemetry

Connection pooling is handled by redis-py library automatically.
"""
import os
import logging
from typing import Optional

import redis.asyncio as redis
from redis.asyncio import Redis

logger = logging.getLogger(__name__)

_redis_client: Optional[Redis] = None


def get_redis_url() -> str:
    """Build Redis connection URL from environment or default."""
    host = os.getenv("REDIS_HOST", "redis")
    port = int(os.getenv("REDIS_PORT", "6379"))
    db = int(os.getenv("REDIS_DB", "0"))
    return f"redis://{host}:{port}/{db}"


async def get_redis() -> Redis:
    """Get or create the global Redis client (lazy initialization)."""
    global _redis_client
    if _redis_client is None:
        url = get_redis_url()
        _redis_client = await redis.from_url(url, encoding="utf-8", decode_responses=True)
        logger.info(f"Redis client connected to {url}")
    return _redis_client


async def close_redis() -> None:
    """Close the Redis connection."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
        logger.info("Redis client closed")
