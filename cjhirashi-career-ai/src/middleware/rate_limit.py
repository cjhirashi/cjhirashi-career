"""
Rate limiting middleware for IA service (FASE 5).

Implements per-user and per-IP rate limiting with configurable windows.
Protects endpoints against abuse and ensures fair resource allocation.

Strategy:
- Track requests by user_id (authenticated) or IP (fallback)
- Use sliding window with TTL for cleanup
- Return 429 Too Many Requests when exceeded
"""

import time
import logging
from typing import Dict, Tuple, Optional
from collections import defaultdict

from fastapi import Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class RateLimiter:
    """In-memory rate limiter with sliding window."""

    def __init__(self, requests_per_window: int = 100, window_size_seconds: int = 60):
        """
        Initialize rate limiter.

        Args:
            requests_per_window: Max requests allowed in window
            window_size_seconds: Size of sliding window in seconds
        """
        self.requests_per_window = requests_per_window
        self.window_size_seconds = window_size_seconds
        self.request_history: Dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, key: str) -> bool:
        """
        Check if request is allowed for given key (user_id or IP).

        Returns:
            True if request is allowed, False if rate limit exceeded
        """
        now = time.time()
        window_start = now - self.window_size_seconds

        # Clean old requests outside window
        if key in self.request_history:
            self.request_history[key] = [
                ts for ts in self.request_history[key]
                if ts > window_start
            ]

        # Check limit
        if len(self.request_history[key]) >= self.requests_per_window:
            logger.warning(f"Rate limit exceeded for {key}")
            return False

        # Add current request
        self.request_history[key].append(now)
        return True

    def get_remaining(self, key: str) -> int:
        """Get remaining requests for key in current window."""
        now = time.time()
        window_start = now - self.window_size_seconds

        if key in self.request_history:
            valid_requests = [
                ts for ts in self.request_history[key]
                if ts > window_start
            ]
            return max(0, self.requests_per_window - len(valid_requests))

        return self.requests_per_window


# Global rate limiters for different endpoints
_global_limiter = RateLimiter(requests_per_window=1000, window_size_seconds=60)  # 1000/min global
_chat_limiter = RateLimiter(requests_per_window=30, window_size_seconds=60)  # 30/min chat
_model_limiter = RateLimiter(requests_per_window=10, window_size_seconds=60)  # 10/min model
_task_limiter = RateLimiter(requests_per_window=50, window_size_seconds=60)  # 50/min tasks


def get_client_id(request: Request) -> str:
    """Extract client identifier (user_id from token or IP)."""
    # Try to get user_id from authorization header
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        # Extract user_id from token (placeholder)
        # TODO: Implement proper JWT extraction
        return f"user:{auth_header[7:40]}"  # First 40 chars of token as key

    # Fallback to IP
    client_ip = (
        request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        or request.client.host
    )
    return f"ip:{client_ip}"


async def rate_limit_middleware(request: Request, call_next):
    """
    Rate limiting middleware.

    Protects endpoints based on type:
    - /chat endpoints: 30 req/min per user
    - /model endpoints: 10 req/min per user
    - /agent-tasks endpoints: 50 req/min per user
    - Other endpoints: 1000 req/min per IP
    """
    client_id = get_client_id(request)
    path = request.url.path

    # Select appropriate limiter based on path
    if "/chat" in path:
        limiter = _chat_limiter
        limit_name = "chat"
    elif "/model" in path:
        limiter = _model_limiter
        limit_name = "model"
    elif "/agent-tasks" in path:
        limiter = _task_limiter
        limit_name = "tasks"
    else:
        limiter = _global_limiter
        limit_name = "global"

    # Check rate limit
    if not limiter.is_allowed(client_id):
        remaining = limiter.get_remaining(client_id)
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "detail": f"Rate limit exceeded ({limit_name})",
                "limit_type": limit_name,
                "remaining": remaining,
                "retry_after": limiter.window_size_seconds,
            },
            headers={
                "Retry-After": str(limiter.window_size_seconds),
            },
        )

    # Add rate limit headers to response
    response = await call_next(request)
    remaining = limiter.get_remaining(client_id)
    response.headers["X-RateLimit-Limit"] = str(limiter.requests_per_window)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(
        int(time.time()) + limiter.window_size_seconds
    )

    return response


async def auth_rate_limit_middleware(request: Request, call_next):
    """Simpler rate limiter that only checks authenticated endpoints."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return await call_next(request)

    client_id = get_client_id(request)
    if not _global_limiter.is_allowed(client_id):
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "detail": "Rate limit exceeded",
                "retry_after": _global_limiter.window_size_seconds,
            },
            headers={
                "Retry-After": str(_global_limiter.window_size_seconds),
            },
        )

    response = await call_next(request)
    remaining = _global_limiter.get_remaining(client_id)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(
        int(time.time()) + _global_limiter.window_size_seconds
    )

    return response
