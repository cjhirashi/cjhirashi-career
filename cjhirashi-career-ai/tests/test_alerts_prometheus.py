"""Tests for alerts and Prometheus metrics (FASE 5)."""

import pytest
from middleware.alerts import RateLimitAlerts


class TestRateLimitAlerts:
    """Test cases for rate limit alert system."""

    def test_alert_on_threshold(self):
        """Test that alert is triggered when violation threshold is reached."""
        alerts = RateLimitAlerts()
        alerts.alert_threshold = 3

        client_id = "test_client"

        # Record violations
        for i in range(2):
            result = alerts.record_violation(client_id, "chat")
            assert result is False  # Not yet at threshold

        # Third violation should trigger alert
        result = alerts.record_violation(client_id, "chat")
        assert result is True

    def test_alert_only_once_per_window(self):
        """Test that alert is only triggered once per client per window."""
        alerts = RateLimitAlerts()
        alerts.alert_threshold = 2

        client_id = "test_client"

        # Trigger first alert
        alerts.record_violation(client_id, "chat")
        result1 = alerts.record_violation(client_id, "chat")
        assert result1 is True

        # Second alert attempt should not trigger
        result2 = alerts.record_violation(client_id, "chat")
        assert result2 is False

    def test_different_clients_independent(self):
        """Test that alerts for different clients are independent."""
        alerts = RateLimitAlerts()
        alerts.alert_threshold = 2

        # Trigger alert for client1
        alerts.record_violation("client1", "chat")
        alerts.record_violation("client1", "chat")

        # client2 should not be affected
        result = alerts.record_violation("client2", "chat")
        assert result is False

    def test_reset_client_alerts(self):
        """Test resetting alerts for a specific client."""
        alerts = RateLimitAlerts()
        alerts.alert_threshold = 2

        client_id = "test_client"

        # Trigger alert
        alerts.record_violation(client_id, "chat")
        alerts.record_violation(client_id, "chat")

        # Reset
        alerts.reset_client_alerts(client_id)

        # Next violation should trigger alert again
        alerts.record_violation(client_id, "chat")
        result = alerts.record_violation(client_id, "chat")
        assert result is True

    def test_get_violation_count(self):
        """Test getting violation count for client."""
        alerts = RateLimitAlerts()

        client_id = "test_client"

        assert alerts.get_violation_count(client_id) == 0

        alerts.record_violation(client_id, "chat")
        assert alerts.get_violation_count(client_id) == 1

        alerts.record_violation(client_id, "chat")
        assert alerts.get_violation_count(client_id) == 2

    def test_get_alert_status(self):
        """Test getting overall alert status."""
        alerts = RateLimitAlerts()
        alerts.alert_threshold = 2

        # Record violations for multiple clients
        alerts.record_violation("client1", "chat")
        alerts.record_violation("client1", "chat")  # Triggers alert

        alerts.record_violation("client2", "chat")

        status = alerts.get_alert_status()

        assert "active_violators" in status
        assert "total_alerted" in status
        assert "violators" in status
        assert status["total_alerted"] == 1


@pytest.mark.asyncio
async def test_prometheus_metrics_format():
    """Test that Prometheus metrics are in correct format."""
    from routes.prometheus import prometheus_metrics

    response = await prometheus_metrics()

    assert response.status_code == 200
    assert response.media_type == "text/plain; version=0.0.4; charset=utf-8"

    content = response.body.decode()

    # Check for expected metrics
    assert "rate_limit_requests" in content
    assert "rate_limit_remaining" in content
    assert "rate_limit_active_clients" in content
    assert "rate_limit_violations" in content
    assert "rate_limit_alerted_clients" in content
    assert "rate_limit_window_seconds" in content
    assert "rate_limit_threshold" in content
    assert "ia_service_up" in content

    # Check format
    assert "# HELP" in content  # Metric help text
    assert "# TYPE" in content  # Metric type
    assert "{limiter=" in content  # Labels


@pytest.mark.asyncio
async def test_prometheus_metrics_contain_limiter_labels():
    """Test that Prometheus metrics include limiter labels."""
    from routes.prometheus import prometheus_metrics

    response = await prometheus_metrics()
    content = response.body.decode()

    # Check for limiter labels
    limiters = ["chat", "model", "task", "global"]
    for limiter in limiters:
        assert f'limiter="{limiter}"' in content


@pytest.mark.asyncio
async def test_prometheus_service_status():
    """Test that Prometheus reports service as up."""
    from routes.prometheus import prometheus_metrics

    response = await prometheus_metrics()
    content = response.body.decode()

    assert "ia_service_up 1" in content
