"""
Alert system for rate limit violations (FASE 5).

Notifies when clients exceed rate limits:
- Logging de eventos críticos
- Potencial integración con Slack/PagerDuty
- Tracking de repeat offenders
"""

import logging
import time
from typing import Dict, Set
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RateLimitAlerts:
    """Manages alerts for rate limit violations."""

    def __init__(self):
        """Initialize alert system."""
        self.violations: Dict[str, list] = {}  # client_id -> list of timestamps
        self.alert_threshold = 5  # Alert after N violations in window
        self.alert_window_seconds = 3600  # 1 hour window
        self.alerted_clients: Set[str] = set()  # Clients already alerted

    def record_violation(self, client_id: str, limiter_name: str) -> bool:
        """
        Record a rate limit violation.

        Returns:
            True if alert should be triggered, False otherwise
        """
        now = time.time()
        window_start = now - self.alert_window_seconds

        # Initialize if needed
        if client_id not in self.violations:
            self.violations[client_id] = []

        # Clean old violations
        self.violations[client_id] = [
            ts for ts in self.violations[client_id]
            if ts > window_start
        ]

        # Add new violation
        self.violations[client_id].append(now)

        # Check if we should alert
        violation_count = len(self.violations[client_id])

        if violation_count >= self.alert_threshold:
            should_alert = client_id not in self.alerted_clients

            if should_alert:
                self.alerted_clients.add(client_id)
                self._send_alert(client_id, limiter_name, violation_count)
                return True

        return False

    def _send_alert(self, client_id: str, limiter_name: str, count: int) -> None:
        """
        Send alert for rate limit violation.

        TODO: Integrate with Slack, PagerDuty, etc.
        """
        timestamp = datetime.now().isoformat()
        logger.critical(
            f"RATE_LIMIT_ALERT: Client {client_id} exceeded {limiter_name} "
            f"limit {count} times in last hour (timestamp: {timestamp})"
        )

    def reset_client_alerts(self, client_id: str) -> None:
        """Reset alert state for client (after manual reset)."""
        if client_id in self.alerted_clients:
            self.alerted_clients.remove(client_id)
        if client_id in self.violations:
            self.violations[client_id].clear()

    def get_violation_count(self, client_id: str) -> int:
        """Get current violation count for client in alert window."""
        if client_id not in self.violations:
            return 0

        now = time.time()
        window_start = now - self.alert_window_seconds
        return len([
            ts for ts in self.violations[client_id]
            if ts > window_start
        ])

    def get_alert_status(self) -> dict:
        """Get current alert status across all clients."""
        now = time.time()
        window_start = now - self.alert_window_seconds

        active_violators = {}
        for client_id, timestamps in self.violations.items():
            valid_violations = [ts for ts in timestamps if ts > window_start]
            if valid_violations:
                active_violators[client_id] = {
                    "violations": len(valid_violations),
                    "alerted": client_id in self.alerted_clients,
                }

        return {
            "active_violators": len(active_violators),
            "total_alerted": len(self.alerted_clients),
            "violators": active_violators,
        }


# Global alert instance
rate_limit_alerts = RateLimitAlerts()
