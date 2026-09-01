"""
Orchestrator client with integrated logging (FASE 6).

Wraps orchestrator_client to add performance logging and tracing.
"""

import time
import logging
from functools import wraps
from typing import Any, Dict, Optional

from clients.orchestrator_client import orchestrator_client
from middleware.logging_config import performance_logger
from middleware.tracing import tracer

logger = logging.getLogger(__name__)


def log_orchestrator_call(operation_name: str):
    """Decorator to log orchestrator API calls with performance metrics."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            trace_id = kwargs.pop("trace_id", None)

            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000

                # Log performance
                performance_logger.log_external_api_call(
                    service_name="orchestrator",
                    endpoint=f"/api/{operation_name}",
                    method="GET" if "get" in func.__name__ else "POST",
                    status_code=200,
                    duration_ms=duration_ms,
                    correlation_id=trace_id or "unknown",
                )

                # Log in trace if available
                if trace_id:
                    tracer.log_external_call(
                        trace_id=trace_id,
                        service_name="orchestrator",
                        endpoint=f"/api/{operation_name}",
                        method="GET" if "get" in func.__name__ else "POST",
                        duration_ms=duration_ms,
                        status_code=200,
                    )

                return result

            except Exception as exc:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(
                    f"Orchestrator call failed: {operation_name}",
                    extra={
                        "trace_id": trace_id or "unknown",
                        "error": str(exc),
                        "duration_ms": duration_ms,
                    }
                )
                raise

        return wrapper

    return decorator


class LoggedOrchestratorClient:
    """Orchestrator client wrapper with logging."""

    def __init__(self, client):
        """Initialize logged client."""
        self.client = client
        self.logger = logging.getLogger("orchestrator")

    async def get_conversations(
        self,
        user_id: str,
        auth_token: str,
        trace_id: Optional[str] = None,
    ):
        """Get conversations with logging."""
        return await self._logged_call(
            self.client.get_conversations,
            "conversations",
            user_id,
            auth_token,
            trace_id=trace_id,
        )

    async def get_conversation_messages(
        self,
        user_id: str,
        auth_token: str,
        session_id: str,
        trace_id: Optional[str] = None,
    ):
        """Get conversation messages with logging."""
        return await self._logged_call(
            self.client.get_conversation_messages,
            f"conversations/{session_id}/messages",
            user_id,
            auth_token,
            session_id,
            trace_id=trace_id,
        )

    async def get_usage_metrics(
        self,
        user_id: str,
        auth_token: str,
        trace_id: Optional[str] = None,
    ):
        """Get usage metrics with logging."""
        return await self._logged_call(
            self.client.get_usage_metrics,
            "usage-metrics",
            user_id,
            auth_token,
            trace_id=trace_id,
        )

    async def execute_task(
        self,
        user_id: str,
        auth_token: str,
        task_id: str,
        trace_id: Optional[str] = None,
    ):
        """Execute task with logging."""
        return await self._logged_call(
            self.client.execute_task,
            f"tasks/{task_id}/run",
            user_id,
            auth_token,
            task_id,
            trace_id=trace_id,
        )

    async def _logged_call(
        self,
        func,
        operation_name: str,
        *args,
        trace_id: Optional[str] = None,
        **kwargs,
    ):
        """Generic logging wrapper for orchestrator calls."""
        start_time = time.time()

        try:
            result = await func(*args, **kwargs)
            duration_ms = (time.time() - start_time) * 1000

            # Log performance
            performance_logger.log_external_api_call(
                service_name="orchestrator",
                endpoint=f"/api/{operation_name}",
                method="GET",
                status_code=200,
                duration_ms=duration_ms,
                correlation_id=trace_id or "unknown",
            )

            # Log in trace if available
            if trace_id:
                tracer.log_external_call(
                    trace_id=trace_id,
                    service_name="orchestrator",
                    endpoint=f"/api/{operation_name}",
                    method="GET",
                    duration_ms=duration_ms,
                    status_code=200,
                )

            return result

        except Exception as exc:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.error(
                f"Orchestrator call failed: {operation_name}",
                extra={
                    "trace_id": trace_id or "unknown",
                    "error": str(exc),
                    "duration_ms": duration_ms,
                }
            )
            raise


# Wrap the global orchestrator_client instance
logged_orchestrator_client = LoggedOrchestratorClient(orchestrator_client)
