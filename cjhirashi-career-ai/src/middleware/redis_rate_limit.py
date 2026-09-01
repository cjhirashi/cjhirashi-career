"""
Redis-backed rate limiter for distributed rate limiting (FASE 5).

Replaces in-memory rate limiter for multi-instance deployments.
Uses sliding window algorithm with Redis sorted sets for efficiency.

Pattern:
- Key format: rate_limit:{limiter_name}:{client_id}
- Value: sorted set of request timestamps
- TTL: Auto-expire after window
"""

import time
import logging
from typing import Optional
import redis
from config import settings

logger = logging.getLogger(__name__)


class RedisRateLimiter:
    """Redis-backed rate limiter with sliding window."""

    def __init__(
        self,
        redis_url: str = "redis://redis:6379/0",
        requests_per_window: int = 100,
        window_size_seconds: int = 60,
        limiter_name: str = "global",
    ):
        """
        Initialize Redis rate limiter.

        Args:
            redis_url: Redis connection URL
            requests_per_window: Max requests in window
            window_size_seconds: Sliding window size
            limiter_name: Name for this limiter (for Redis keys)
        """
        self.redis_url = redis_url
        self.requests_per_window = requests_per_window
        self.window_size_seconds = window_size_seconds
        self.limiter_name = limiter_name
        self.redis_client: Optional[redis.Redis] = None

        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.redis_client.ping()
            logger.info(f"Redis rate limiter '{limiter_name}' initialized successfully")
        except Exception as e:
            logger.warning(f"Redis connection failed for '{limiter_name}': {e}. Falling back to in-memory.")
            self.redis_client = None

    def _get_key(self, client_id: str) -> str:
        """Get Redis key for client."""
        return f"rate_limit:{self.limiter_name}:{client_id}"

    def is_allowed(self, client_id: str) -> bool:
        """
        Check if request is allowed for client.

        Returns:
            True if allowed, False if rate limit exceeded
        """
        if not self.redis_client:
            logger.warning(f"Redis not available for '{self.limiter_name}'")
            return True

        try:
            key = self._get_key(client_id)
            now = time.time()
            window_start = now - self.window_size_seconds

            pipe = self.redis_client.pipeline()

            # Remove old entries outside window
            pipe.zremrangebyscore(key, 0, window_start)

            # Count current requests
            pipe.zcard(key)

            # Execute pipeline
            results = pipe.execute()
            request_count = results[1]

            if request_count >= self.requests_per_window:
                logger.warning(
                    f"Rate limit exceeded for '{self.limiter_name}' client {client_id}: "
                    f"{request_count}/{self.requests_per_window}"
                )
                return False

            # Add current request
            self.redis_client.zadd(key, {str(now): now})

            # Set expiration
            self.redis_client.expire(key, self.window_size_seconds + 1)

            return True

        except Exception as e:
            logger.error(f"Redis error in rate limiter '{self.limiter_name}': {e}")
            return True  # Fail open - allow request if Redis fails

    def get_remaining(self, client_id: str) -> int:
        """Get remaining requests for client in current window."""
        if not self.redis_client:
            return self.requests_per_window

        try:
            key = self._get_key(client_id)
            now = time.time()
            window_start = now - self.window_size_seconds

            # Count valid requests
            request_count = self.redis_client.zcount(key, window_start, now)
            return max(0, self.requests_per_window - request_count)

        except Exception as e:
            logger.error(f"Redis error getting remaining for '{self.limiter_name}': {e}")
            return self.requests_per_window

    def get_client_requests(self, client_id: str) -> int:
        """Get current request count for client."""
        if not self.redis_client:
            return 0

        try:
            key = self._get_key(client_id)
            now = time.time()
            window_start = now - self.window_size_seconds
            return self.redis_client.zcount(key, window_start, now)
        except Exception as e:
            logger.error(f"Redis error getting requests for '{self.limiter_name}': {e}")
            return 0

    def get_all_clients(self) -> dict:
        """Get rate limit stats for all active clients."""
        if not self.redis_client:
            return {}

        try:
            pattern = f"rate_limit:{self.limiter_name}:*"
            keys = self.redis_client.keys(pattern)

            stats = {}
            now = time.time()
            window_start = now - self.window_size_seconds

            for key in keys:
                client_id = key.split(":")[-1]
                count = self.redis_client.zcount(key, window_start, now)
                remaining = max(0, self.requests_per_window - count)
                stats[client_id] = {
                    "requests": count,
                    "remaining": remaining,
                    "limit": self.requests_per_window,
                }

            return stats
        except Exception as e:
            logger.error(f"Redis error getting all clients for '{self.limiter_name}': {e}")
            return {}

    def reset_client(self, client_id: str) -> bool:
        """Reset rate limit for specific client (admin operation)."""
        if not self.redis_client:
            return False

        try:
            key = self._get_key(client_id)
            self.redis_client.delete(key)
            logger.info(f"Rate limit reset for '{self.limiter_name}' client {client_id}")
            return True
        except Exception as e:
            logger.error(f"Redis error resetting client '{client_id}': {e}")
            return False

    def reset_all(self) -> bool:
        """Reset all rate limits for this limiter (admin operation)."""
        if not self.redis_client:
            return False

        try:
            pattern = f"rate_limit:{self.limiter_name}:*"
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
            logger.info(f"Rate limit reset for all clients in '{self.limiter_name}'")
            return True
        except Exception as e:
            logger.error(f"Redis error resetting all for '{self.limiter_name}': {e}")
            return False
