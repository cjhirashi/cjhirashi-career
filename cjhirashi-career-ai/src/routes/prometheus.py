"""
Prometheus metrics endpoint for monitoring (FASE 5).

Exports metrics in Prometheus text format for Grafana integration.
Includes rate limit metrics, endpoint statistics, and system health.

Format: https://prometheus.io/docs/instrumenting/exposition_formats/
"""

from fastapi import APIRouter, status
from fastapi.responses import Response
import time

from middleware.rate_limit import _chat_limiter, _model_limiter, _task_limiter, _global_limiter
from middleware.alerts import rate_limit_alerts

router = APIRouter(prefix="/metrics/prometheus", tags=["Prometheus"])


def _format_prometheus_metric(metric_name: str, value, labels: dict = None) -> str:
    """Format a metric in Prometheus text format."""
    if labels:
        label_str = ",".join([f'{k}="{v}"' for k, v in labels.items()])
        return f'{metric_name}{{{label_str}}} {value}\n'
    return f'{metric_name} {value}\n'


@router.get("/", response_class=Response, summary="Prometheus metrics export")
async def prometheus_metrics():
    """
    Export all metrics in Prometheus text format.

    Usage with Grafana:
    1. Add data source: http://localhost:8010/api/metrics/prometheus
    2. Create dashboard with queries like:
       - rate_limit_requests{limiter="chat"}
       - rate_limit_remaining{limiter="chat"}
    """
    metrics = []
    timestamp_ms = int(time.time() * 1000)

    # =========================================================================
    # RATE LIMITING METRICS
    # =========================================================================

    metrics.append("# HELP rate_limit_requests Current requests in window\n")
    metrics.append("# TYPE rate_limit_requests gauge\n")

    for limiter_name, limiter in [
        ("chat", _chat_limiter),
        ("model", _model_limiter),
        ("task", _task_limiter),
        ("global", _global_limiter),
    ]:
        total_requests = sum(len(reqs) for reqs in limiter.request_history.values())
        metrics.append(
            _format_prometheus_metric(
                "rate_limit_requests",
                total_requests,
                {"limiter": limiter_name}
            )
        )

    # =========================================================================
    # RATE LIMIT REMAINING
    # =========================================================================

    metrics.append("\n# HELP rate_limit_remaining Remaining requests in current window\n")
    metrics.append("# TYPE rate_limit_remaining gauge\n")

    for limiter_name, limiter in [
        ("chat", _chat_limiter),
        ("model", _model_limiter),
        ("task", _task_limiter),
        ("global", _global_limiter),
    ]:
        total_remaining = sum(
            limiter.get_remaining(client_id)
            for client_id in limiter.request_history.keys()
        )
        metrics.append(
            _format_prometheus_metric(
                "rate_limit_remaining",
                total_remaining,
                {"limiter": limiter_name}
            )
        )

    # =========================================================================
    # ACTIVE CLIENTS
    # =========================================================================

    metrics.append("\n# HELP rate_limit_active_clients Number of active clients\n")
    metrics.append("# TYPE rate_limit_active_clients gauge\n")

    for limiter_name, limiter in [
        ("chat", _chat_limiter),
        ("model", _model_limiter),
        ("task", _task_limiter),
        ("global", _global_limiter),
    ]:
        active_clients = len(limiter.request_history)
        metrics.append(
            _format_prometheus_metric(
                "rate_limit_active_clients",
                active_clients,
                {"limiter": limiter_name}
            )
        )

    # =========================================================================
    # RATE LIMIT VIOLATIONS
    # =========================================================================

    metrics.append("\n# HELP rate_limit_violations Total rate limit violations\n")
    metrics.append("# TYPE rate_limit_violations counter\n")

    alert_status = rate_limit_alerts.get_alert_status()
    metrics.append(
        _format_prometheus_metric(
            "rate_limit_violations",
            alert_status["active_violators"]
        )
    )

    # =========================================================================
    # RATE LIMIT ALERTS
    # =========================================================================

    metrics.append("\n# HELP rate_limit_alerted_clients Clients with active alerts\n")
    metrics.append("# TYPE rate_limit_alerted_clients gauge\n")

    metrics.append(
        _format_prometheus_metric(
            "rate_limit_alerted_clients",
            alert_status["total_alerted"]
        )
    )

    # =========================================================================
    # WINDOW SIZE
    # =========================================================================

    metrics.append("\n# HELP rate_limit_window_seconds Rate limit window size in seconds\n")
    metrics.append("# TYPE rate_limit_window_seconds gauge\n")

    for limiter_name, limiter in [
        ("chat", _chat_limiter),
        ("model", _model_limiter),
        ("task", _task_limiter),
        ("global", _global_limiter),
    ]:
        metrics.append(
            _format_prometheus_metric(
                "rate_limit_window_seconds",
                limiter.window_size_seconds,
                {"limiter": limiter_name}
            )
        )

    # =========================================================================
    # LIMIT THRESHOLD
    # =========================================================================

    metrics.append("\n# HELP rate_limit_threshold Maximum requests per window\n")
    metrics.append("# TYPE rate_limit_threshold gauge\n")

    for limiter_name, limiter in [
        ("chat", _chat_limiter),
        ("model", _model_limiter),
        ("task", _task_limiter),
        ("global", _global_limiter),
    ]:
        metrics.append(
            _format_prometheus_metric(
                "rate_limit_threshold",
                limiter.requests_per_window,
                {"limiter": limiter_name}
            )
        )

    # =========================================================================
    # SERVICE METRICS
    # =========================================================================

    metrics.append("\n# HELP ia_service_up Service is up and running\n")
    metrics.append("# TYPE ia_service_up gauge\n")
    metrics.append(_format_prometheus_metric("ia_service_up", 1))

    metrics.append("\n# HELP ia_service_timestamp Current timestamp\n")
    metrics.append("# TYPE ia_service_timestamp gauge\n")
    metrics.append(_format_prometheus_metric("ia_service_timestamp", time.time()))

    return Response(
        content="".join(metrics),
        media_type="text/plain; version=0.0.4; charset=utf-8",
        status_code=status.HTTP_200_OK,
    )
