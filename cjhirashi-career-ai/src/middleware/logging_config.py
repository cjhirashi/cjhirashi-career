"""
Structured logging configuration for FASE 6.

Implements JSON logging for better observability and log aggregation.
Includes request/response tracking with correlation IDs.
"""

import json
import logging
import time
from typing import Optional
import uuid
from datetime import datetime

try:
    from pythonjsonlogger import jsonlogger
except ImportError:
    jsonlogger = None


class StructuredFormatter(logging.Formatter if jsonlogger is None else jsonlogger.JsonFormatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record):
        """Format log record as JSON."""
        if jsonlogger is None:
            # Fallback to standard formatting if pythonjsonlogger not available
            log_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "process_id": record.process,
                "thread_id": record.thread,
            }
            return json.dumps(log_data)

        return super().format(record)

    def add_fields(self, log_record, record, message_dict):
        """Add custom fields to log record."""
        if jsonlogger is None:
            return

        super().add_fields(log_record, record, message_dict)

        # Add timestamp in ISO format
        log_record["timestamp"] = datetime.utcnow().isoformat()

        # Add logger name and level
        log_record["logger"] = record.name
        log_record["level"] = record.levelname

        # Add process and thread info
        log_record["process_id"] = record.process
        log_record["thread_id"] = record.thread

        # Add exception info if present
        if record.exc_info:
            log_record["exception"] = self.format_exception(record.exc_info)


def setup_logging(level: str = "INFO") -> None:
    """
    Setup structured JSON logging for the application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Remove existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler with JSON formatter
    handler = logging.StreamHandler()

    if jsonlogger is not None:
        formatter = StructuredFormatter(
            "%(timestamp)s %(level)s %(logger)s %(message)s",
            timestamp=True
        )
    else:
        # Fallback formatter when pythonjsonlogger not available
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    handler.setFormatter(formatter)

    # Configure root logger
    root_logger.addHandler(handler)
    root_logger.setLevel(level)

    # Suppress noisy loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)


class RequestLogger:
    """Logger for HTTP requests with correlation IDs."""

    def __init__(self):
        """Initialize request logger."""
        self.logger = logging.getLogger("http_request")
        self._request_context = {}

    def get_correlation_id(self) -> str:
        """Get or generate correlation ID for request tracking."""
        return str(uuid.uuid4())

    def log_request(
        self,
        method: str,
        path: str,
        correlation_id: str,
        user_id: Optional[str] = None,
        client_ip: Optional[str] = None,
    ) -> None:
        """Log incoming HTTP request."""
        self.logger.info(
            "HTTP_REQUEST_RECEIVED",
            extra={
                "correlation_id": correlation_id,
                "method": method,
                "path": path,
                "user_id": user_id or "anonymous",
                "client_ip": client_ip,
                "timestamp": time.time(),
            }
        )

    def log_response(
        self,
        correlation_id: str,
        status_code: int,
        response_time_ms: float,
        response_size: int = 0,
    ) -> None:
        """Log outgoing HTTP response."""
        self.logger.info(
            "HTTP_RESPONSE_SENT",
            extra={
                "correlation_id": correlation_id,
                "status_code": status_code,
                "response_time_ms": response_time_ms,
                "response_size": response_size,
                "timestamp": time.time(),
            }
        )

    def log_error(
        self,
        correlation_id: str,
        error_type: str,
        error_message: str,
        stack_trace: Optional[str] = None,
    ) -> None:
        """Log error with correlation ID."""
        self.logger.error(
            "HTTP_ERROR",
            extra={
                "correlation_id": correlation_id,
                "error_type": error_type,
                "error_message": error_message,
                "stack_trace": stack_trace,
                "timestamp": time.time(),
            }
        )


class PerformanceLogger:
    """Logger for performance metrics."""

    def __init__(self):
        """Initialize performance logger."""
        self.logger = logging.getLogger("performance")

    def log_database_query(
        self,
        query_type: str,
        query_name: str,
        duration_ms: float,
        correlation_id: str,
    ) -> None:
        """Log database query performance."""
        self.logger.info(
            "DATABASE_QUERY",
            extra={
                "correlation_id": correlation_id,
                "query_type": query_type,
                "query_name": query_name,
                "duration_ms": duration_ms,
                "slow_query": duration_ms > 1000,  # Queries > 1s are slow
            }
        )

    def log_external_api_call(
        self,
        service_name: str,
        endpoint: str,
        method: str,
        status_code: int,
        duration_ms: float,
        correlation_id: str,
    ) -> None:
        """Log external API call performance."""
        self.logger.info(
            "EXTERNAL_API_CALL",
            extra={
                "correlation_id": correlation_id,
                "service_name": service_name,
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
                "duration_ms": duration_ms,
                "slow_call": duration_ms > 5000,  # Calls > 5s are slow
            }
        )

    def log_rate_limit_check(
        self,
        client_id: str,
        limiter_name: str,
        allowed: bool,
        remaining: int,
        check_time_ms: float,
        correlation_id: str,
    ) -> None:
        """Log rate limit check."""
        self.logger.info(
            "RATE_LIMIT_CHECK",
            extra={
                "correlation_id": correlation_id,
                "client_id": client_id,
                "limiter_name": limiter_name,
                "allowed": allowed,
                "remaining": remaining,
                "check_time_ms": check_time_ms,
            }
        )


# Global logger instances
request_logger = RequestLogger()
performance_logger = PerformanceLogger()
