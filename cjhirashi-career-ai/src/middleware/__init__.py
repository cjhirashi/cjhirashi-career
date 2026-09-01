"""Middleware for IA service (FASE 5 - Rate Limiting)."""

from middleware.rate_limit import (
    rate_limit_middleware,
    auth_rate_limit_middleware,
    RateLimiter,
)

__all__ = [
    "rate_limit_middleware",
    "auth_rate_limit_middleware",
    "RateLimiter",
]
