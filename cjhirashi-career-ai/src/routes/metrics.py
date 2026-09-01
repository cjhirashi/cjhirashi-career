"""
Metrics endpoints for monitoring rate limiting and system health (FASE 5).

Provides observability into:
- Rate limit status per client
- System health metrics
- Resource usage
"""

from fastapi import APIRouter, Request, HTTPException, status
from typing import Dict, Any, List
import logging

from middleware.rate_limit import _chat_limiter, _model_limiter, _task_limiter, _global_limiter
from clients.orchestrator_client import orchestrator_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/metrics", tags=["Metrics"])


def get_auth_token(request: Request) -> str:
    """Extract Bearer token from Authorization header."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header"
        )
    return auth[7:]


def extract_user_id_from_token(auth_token: str) -> str:
    """Extract user_id from JWT token."""
    return "usr-2"  # PLACEHOLDER


@router.get("/rate-limit/status", summary="Get current rate limit status")
async def get_rate_limit_status(request: Request):
    """Get rate limit status for current client."""
    auth_token = get_auth_token(request)
    user_id = extract_user_id_from_token(auth_token)

    # Get client identifier (same as middleware)
    from middleware.rate_limit import get_client_id
    client_id = get_client_id(request)

    return {
        "client_id": client_id,
        "user_id": user_id,
        "limiters": {
            "chat": {
                "remaining": _chat_limiter.get_remaining(client_id),
                "limit": _chat_limiter.requests_per_window,
                "window_seconds": _chat_limiter.window_size_seconds,
            },
            "model": {
                "remaining": _model_limiter.get_remaining(client_id),
                "limit": _model_limiter.requests_per_window,
                "window_seconds": _model_limiter.window_size_seconds,
            },
            "task": {
                "remaining": _task_limiter.get_remaining(client_id),
                "limit": _task_limiter.requests_per_window,
                "window_seconds": _task_limiter.window_size_seconds,
            },
            "global": {
                "remaining": _global_limiter.get_remaining(client_id),
                "limit": _global_limiter.requests_per_window,
                "window_seconds": _global_limiter.window_size_seconds,
            },
        },
    }


@router.get("/rate-limit/all", summary="Get rate limit stats for all clients")
async def get_all_rate_limit_stats(request: Request):
    """Get rate limit stats for all active clients (admin only)."""
    auth_token = get_auth_token(request)
    # TODO: Check admin role

    return {
        "timestamp": __import__("time").time(),
        "chat": {
            "clients": len(_chat_limiter.request_history),
            "requests_total": sum(len(reqs) for reqs in _chat_limiter.request_history.values()),
        },
        "model": {
            "clients": len(_model_limiter.request_history),
            "requests_total": sum(len(reqs) for reqs in _model_limiter.request_history.values()),
        },
        "task": {
            "clients": len(_task_limiter.request_history),
            "requests_total": sum(len(reqs) for reqs in _task_limiter.request_history.values()),
        },
        "global": {
            "clients": len(_global_limiter.request_history),
            "requests_total": sum(len(reqs) for reqs in _global_limiter.request_history.values()),
        },
    }


@router.get("/health", summary="Service health check")
async def health_check():
    """Check IA service health and dependencies."""
    try:
        # Check orchestrator connectivity
        orchestrator_status = "healthy"
        # TODO: Implement actual health check to orchestrator
    except Exception as e:
        orchestrator_status = f"degraded: {str(e)}"

    return {
        "status": "healthy" if orchestrator_status == "healthy" else "degraded",
        "service": "cjhirashi-career-ai",
        "components": {
            "api": "healthy",
            "orchestrator": orchestrator_status,
            "rate_limiting": "healthy",
        },
        "timestamp": __import__("time").time(),
    }


@router.get("/endpoints", summary="List all available endpoints")
async def list_endpoints(request: Request):
    """List all available endpoints with rate limit info."""
    auth_token = get_auth_token(request)

    return {
        "endpoints": [
            {
                "path": "/api/bedrock/chat",
                "method": "POST",
                "rate_limit": "30 req/min",
                "description": "Chat with Agent Bedrock (SSE)",
            },
            {
                "path": "/api/bedrock/model",
                "method": "GET",
                "rate_limit": "10 req/min",
                "description": "Get current model",
            },
            {
                "path": "/api/bedrock/model",
                "method": "POST",
                "rate_limit": "10 req/min",
                "description": "Switch model",
            },
            {
                "path": "/api/bedrock/conversations",
                "method": "GET",
                "rate_limit": "1000 req/min",
                "description": "List conversations",
            },
            {
                "path": "/api/bedrock/memory",
                "method": "GET",
                "rate_limit": "1000 req/min",
                "description": "Get memory records",
            },
            {
                "path": "/api/agent-tasks/{id}/run",
                "method": "POST",
                "rate_limit": "50 req/min",
                "description": "Execute agent task",
            },
        ],
        "total": 20,
    }
