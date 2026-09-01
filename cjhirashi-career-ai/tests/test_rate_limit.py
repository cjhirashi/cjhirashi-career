"""Tests for rate limiting middleware (FASE 5)."""

import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch

from middleware.rate_limit import RateLimiter, get_client_id


class TestRateLimiter:
    """Test cases for RateLimiter class."""

    def test_allows_requests_within_limit(self):
        """Test that requests within limit are allowed."""
        limiter = RateLimiter(requests_per_window=5, window_size_seconds=60)
        key = "test_user"

        for i in range(5):
            assert limiter.is_allowed(key) is True

    def test_blocks_requests_exceeding_limit(self):
        """Test that requests exceeding limit are blocked."""
        limiter = RateLimiter(requests_per_window=3, window_size_seconds=60)
        key = "test_user"

        for i in range(3):
            assert limiter.is_allowed(key) is True

        # Fourth request should be blocked
        assert limiter.is_allowed(key) is False

    def test_sliding_window_cleanup(self):
        """Test that old requests are cleaned up outside window."""
        limiter = RateLimiter(requests_per_window=2, window_size_seconds=1)
        key = "test_user"

        # Make 2 requests at t=0
        assert limiter.is_allowed(key) is True
        assert limiter.is_allowed(key) is True

        # Third request blocked at t=0
        assert limiter.is_allowed(key) is False

        # Wait for window to expire
        time.sleep(1.1)

        # Request should now be allowed (window cleared)
        assert limiter.is_allowed(key) is True

    def test_different_keys_independent(self):
        """Test that different keys don't affect each other."""
        limiter = RateLimiter(requests_per_window=2, window_size_seconds=60)

        assert limiter.is_allowed("user1") is True
        assert limiter.is_allowed("user1") is True
        assert limiter.is_allowed("user1") is False

        # user2 should not be affected
        assert limiter.is_allowed("user2") is True
        assert limiter.is_allowed("user2") is True
        assert limiter.is_allowed("user2") is False

    def test_get_remaining(self):
        """Test remaining requests calculation."""
        limiter = RateLimiter(requests_per_window=5, window_size_seconds=60)
        key = "test_user"

        assert limiter.get_remaining(key) == 5

        limiter.is_allowed(key)
        assert limiter.get_remaining(key) == 4

        limiter.is_allowed(key)
        assert limiter.get_remaining(key) == 3

        limiter.is_allowed(key)
        limiter.is_allowed(key)
        limiter.is_allowed(key)
        assert limiter.get_remaining(key) == 0


class TestGetClientId:
    """Test cases for client ID extraction."""

    def test_extract_id_from_bearer_token(self):
        """Test extracting client ID from Bearer token."""
        request = MagicMock()
        request.headers.get.return_value = "Bearer abc123def456ghi789jkl012mno345pqr"

        client_id = get_client_id(request)
        assert client_id.startswith("user:")
        assert "abc123def456ghi" in client_id

    def test_fallback_to_ip_without_auth(self):
        """Test falling back to IP when no auth header."""
        request = MagicMock()
        request.headers.get.return_value = ""
        request.headers.get.side_effect = lambda k, d="": d if k == "Authorization" else ""
        request.client.host = "192.168.1.100"

        client_id = get_client_id(request)
        assert client_id.startswith("ip:")
        assert "192.168.1.100" in client_id

    def test_extract_from_x_forwarded_for(self):
        """Test extracting IP from X-Forwarded-For header."""
        request = MagicMock()
        request.headers.get.side_effect = lambda k, d="": (
            "203.0.113.1, 203.0.113.2" if k == "X-Forwarded-For" else d
        )
        request.client.host = "192.168.1.100"

        client_id = get_client_id(request)
        assert client_id.startswith("ip:")
        assert "203.0.113.1" in client_id


@pytest.mark.asyncio
async def test_rate_limit_middleware_allows_within_limit():
    """Test that middleware allows requests within limit."""
    from middleware.rate_limit import rate_limit_middleware

    request = MagicMock()
    request.headers.get.return_value = ""
    request.headers.get.side_effect = lambda k, d="": d if k == "Authorization" else ""
    request.client.host = "192.168.1.100"
    request.url.path = "/api/bedrock/model"

    call_next = AsyncMock(return_value=MagicMock(headers={}))

    # Make requests within limit
    for _ in range(5):
        response = await rate_limit_middleware(request, call_next)
        assert response.status_code != 429


@pytest.mark.asyncio
async def test_rate_limit_middleware_blocks_exceeding_limit():
    """Test that middleware blocks requests exceeding limit."""
    from middleware.rate_limit import rate_limit_middleware, _global_limiter

    # Clear previous state
    _global_limiter.request_history.clear()

    request = MagicMock()
    request.headers.get.return_value = ""
    request.headers.get.side_effect = lambda k, d="": d if k == "Authorization" else ""
    request.client.host = "192.168.1.100"
    request.url.path = "/api/bedrock/model"

    call_next = AsyncMock(return_value=MagicMock(headers={}))

    # Make requests
    for _ in range(_global_limiter.requests_per_window):
        response = await rate_limit_middleware(request, call_next)
        if response.status_code == 429:
            break

    # Next request should be rate limited
    response = await rate_limit_middleware(request, call_next)
    assert response.status_code == 429
    assert "Rate limit exceeded" in response.body.decode()
