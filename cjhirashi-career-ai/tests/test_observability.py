"""Tests for observability dashboard (FASE 6)."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from routes.observability import service_info


@pytest.mark.asyncio
async def test_service_info():
    """Test service info endpoint."""
    response = await service_info()

    assert response["service_name"] == "cjhirashi-career-ai"
    assert response["version"] == "1.0.0"
    assert "features" in response
    assert "capabilities" in response

    # Check features
    assert response["features"]["rate_limiting"] is True
    assert response["features"]["structured_logging"] is True
    assert response["features"]["distributed_tracing"] is True

    # Check capabilities
    assert response["capabilities"]["endpoints"] == 25
    assert response["capabilities"]["middlewares"] == 5


@pytest.mark.asyncio
async def test_dashboard_requires_auth():
    """Test that dashboard requires authentication."""
    from routes.observability import observability_dashboard

    request = MagicMock()
    request.headers.get.return_value = ""

    with pytest.raises(Exception):  # Should raise HTTPException
        await observability_dashboard(request)


@pytest.mark.asyncio
async def test_performance_metrics_requires_auth():
    """Test that performance metrics requires authentication."""
    from routes.observability import performance_metrics

    request = MagicMock()
    request.headers.get.return_value = ""

    with pytest.raises(Exception):  # Should raise HTTPException
        await performance_metrics(request)


@pytest.mark.asyncio
async def test_trace_details_not_found():
    """Test getting non-existent trace."""
    from routes.observability import get_trace_details

    request = MagicMock()
    request.headers.get.side_effect = lambda k, d="": (
        "Bearer token123" if k == "Authorization" else ""
    )

    with pytest.raises(Exception):  # Should raise HTTPException 404
        await get_trace_details("non-existent-trace", request)
