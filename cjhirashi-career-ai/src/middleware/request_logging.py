"""
Request/Response logging middleware for FASE 6.

Logs all HTTP requests and responses with performance metrics.
Adds correlation IDs for distributed tracing.
"""

import time
import logging
from typing import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from middleware.logging_config import request_logger

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests and responses with correlation IDs."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response."""
        # Generate or extract correlation ID
        correlation_id = request.headers.get("X-Correlation-ID") or request.scope.get(
            "correlation_id"
        )
        if not correlation_id:
            correlation_id = request_logger.get_correlation_id()

        # Store correlation ID in request state for downstream use
        request.state.correlation_id = correlation_id

        # Extract user info
        user_id = None
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            user_id = auth_header[7:40]  # First 40 chars as identifier

        # Get client IP
        client_ip = (
            request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            or request.client.host
        )

        # Log incoming request
        start_time = time.time()
        request_logger.log_request(
            method=request.method,
            path=request.url.path,
            correlation_id=correlation_id,
            user_id=user_id,
            client_ip=client_ip,
        )

        try:
            # Call the next middleware/endpoint
            response = await call_next(request)

            # Calculate response time
            response_time_ms = (time.time() - start_time) * 1000

            # Log outgoing response
            request_logger.log_response(
                correlation_id=correlation_id,
                status_code=response.status_code,
                response_time_ms=response_time_ms,
            )

            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id

            return response

        except Exception as exc:
            # Log error
            response_time_ms = (time.time() - start_time) * 1000
            request_logger.log_error(
                correlation_id=correlation_id,
                error_type=type(exc).__name__,
                error_message=str(exc),
            )

            # Re-raise the exception
            raise
