"""Tests for metrics endpoints (FASE 5)."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient


@pytest.mark.asyncio
async def test_rate_limit_status_requires_auth():
    """Test that rate limit status endpoint requires authentication."""
    from routes.metrics import get_rate_limit_status
    from fastapi import Request, HTTPException

    request = MagicMock()
    request.headers.get.return_value = ""

    with pytest.raises(HTTPException) as exc_info:
        await get_rate_limit_status(request)

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_rate_limit_status_returns_metrics():
    """Test that rate limit status returns correct structure."""
    from routes.metrics import get_rate_limit_status, get_auth_token

    request = MagicMock()
    request.headers.get.side_effect = lambda k, d="": (
        "Bearer token123" if k == "Authorization" else ""
    )
    request.client.host = "192.168.1.100"

    response = await get_rate_limit_status(request)

    assert "client_id" in response
    assert "user_id" in response
    assert "limiters" in response
    assert "chat" in response["limiters"]
    assert "model" in response["limiters"]
    assert "task" in response["limiters"]
    assert "global" in response["limiters"]

    # Check limiter structure
    for limiter_name, limiter_data in response["limiters"].items():
        assert "remaining" in limiter_data
        assert "limit" in limiter_data
        assert "window_seconds" in limiter_data
        assert isinstance(limiter_data["remaining"], int)
        assert isinstance(limiter_data["limit"], int)


@pytest.mark.asyncio
async def test_health_check_returns_status():
    """Test that health check endpoint returns service status."""
    from routes.metrics import health_check

    response = await health_check()

    assert "status" in response
    assert "service" in response
    assert "components" in response
    assert "timestamp" in response
    assert response["service"] == "cjhirashi-career-ai"
    assert response["status"] in ["healthy", "degraded"]


@pytest.mark.asyncio
async def test_list_endpoints_requires_auth():
    """Test that list endpoints requires authentication."""
    from routes.metrics import list_endpoints

    request = MagicMock()
    request.headers.get.return_value = ""

    with pytest.raises(Exception):  # Should raise HTTPException
        await list_endpoints(request)


@pytest.mark.asyncio
async def test_list_endpoints_returns_endpoint_list():
    """Test that list endpoints returns correct structure."""
    from routes.metrics import list_endpoints

    request = MagicMock()
    request.headers.get.side_effect = lambda k, d="": (
        "Bearer token123" if k == "Authorization" else ""
    )

    response = await list_endpoints(request)

    assert "endpoints" in response
    assert "total" in response
    assert isinstance(response["endpoints"], list)
    assert len(response["endpoints"]) > 0

    # Check endpoint structure
    for endpoint in response["endpoints"]:
        assert "path" in endpoint
        assert "method" in endpoint
        assert "rate_limit" in endpoint
        assert "description" in endpoint


@pytest.mark.asyncio
async def test_all_rate_limit_stats_requires_auth():
    """Test that rate limit stats endpoint requires auth."""
    from routes.metrics import get_all_rate_limit_stats

    request = MagicMock()
    request.headers.get.return_value = ""

    with pytest.raises(Exception):
        await get_all_rate_limit_stats(request)


@pytest.mark.asyncio
async def test_all_rate_limit_stats_returns_stats():
    """Test that rate limit stats returns correct structure."""
    from routes.metrics import get_all_rate_limit_stats

    request = MagicMock()
    request.headers.get.side_effect = lambda k, d="": (
        "Bearer token123" if k == "Authorization" else ""
    )

    response = await get_all_rate_limit_stats(request)

    assert "timestamp" in response
    assert "chat" in response
    assert "model" in response
    assert "task" in response
    assert "global" in response

    # Check stats structure
    for limiter_name, stats in [
        ("chat", response["chat"]),
        ("model", response["model"]),
        ("task", response["task"]),
        ("global", response["global"]),
    ]:
        assert "clients" in stats
        assert "requests_total" in stats
        assert isinstance(stats["clients"], int)
        assert isinstance(stats["requests_total"], int)
