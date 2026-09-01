"""
OpenTelemetry distributed tracing for FASE 6.

Enables request tracing across microservices.
Compatible with Jaeger, Zipkin, and cloud tracing backends.

TODO: Full OpenTelemetry integration when available
Current: Mock tracing infrastructure for planning
"""

import time
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class Span:
    """Represents a single span in a trace."""

    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    operation_name: str
    start_time: float
    end_time: Optional[float] = None
    tags: Dict[str, Any] = None
    logs: Dict[str, Any] = None
    status: str = "UNSET"  # UNSET, OK, ERROR

    def __post_init__(self):
        """Initialize default values."""
        if self.tags is None:
            self.tags = {}
        if self.logs is None:
            self.logs = {}

    def set_tag(self, key: str, value: Any) -> None:
        """Add a tag to the span."""
        self.tags[key] = value

    def add_log(self, key: str, value: Any) -> None:
        """Add a log entry to the span."""
        self.logs[key] = value

    def finish(self, status: str = "OK") -> None:
        """Mark span as finished."""
        self.end_time = time.time()
        self.status = status

    @property
    def duration_ms(self) -> float:
        """Get span duration in milliseconds."""
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return 0


class TracingContext:
    """Manages tracing context for requests."""

    def __init__(self, trace_id: str, root_span_id: str):
        """Initialize tracing context."""
        self.trace_id = trace_id
        self.root_span_id = root_span_id
        self.current_span_id = root_span_id
        self.spans: Dict[str, Span] = {}

    def create_span(
        self,
        operation_name: str,
        parent_span_id: Optional[str] = None,
    ) -> Span:
        """Create a new span."""
        import uuid

        span_id = str(uuid.uuid4())[:16]
        parent = parent_span_id or self.current_span_id

        span = Span(
            trace_id=self.trace_id,
            span_id=span_id,
            parent_span_id=parent,
            operation_name=operation_name,
            start_time=time.time(),
        )

        self.spans[span_id] = span
        return span

    def get_spans(self) -> list:
        """Get all spans in this trace."""
        return list(self.spans.values())

    def to_dict(self) -> Dict[str, Any]:
        """Convert trace to dictionary for export."""
        return {
            "trace_id": self.trace_id,
            "root_span_id": self.root_span_id,
            "spans": [
                {
                    "span_id": span.span_id,
                    "parent_span_id": span.parent_span_id,
                    "operation_name": span.operation_name,
                    "duration_ms": span.duration_ms,
                    "status": span.status,
                    "tags": span.tags,
                }
                for span in self.spans.values()
            ],
        }


class TracingManager:
    """Manages distributed tracing for the application."""

    def __init__(self):
        """Initialize tracing manager."""
        self.active_traces: Dict[str, TracingContext] = {}
        self.logger = logging.getLogger("tracing")

    def create_trace(self) -> str:
        """Create a new trace and return trace ID."""
        import uuid

        trace_id = str(uuid.uuid4())
        root_span_id = str(uuid.uuid4())[:16]

        context = TracingContext(trace_id, root_span_id)
        self.active_traces[trace_id] = context

        self.logger.info(f"Trace created: {trace_id}")
        return trace_id

    def get_trace(self, trace_id: str) -> Optional[TracingContext]:
        """Get tracing context for trace ID."""
        return self.active_traces.get(trace_id)

    def end_trace(self, trace_id: str) -> Dict[str, Any]:
        """End a trace and return its data."""
        context = self.active_traces.pop(trace_id, None)
        if not context:
            return {}

        trace_data = context.to_dict()
        self.logger.info(f"Trace ended: {trace_id}")
        return trace_data

    def log_external_call(
        self,
        trace_id: str,
        service_name: str,
        endpoint: str,
        method: str,
        duration_ms: float,
        status_code: int,
    ) -> None:
        """Log an external service call in the trace."""
        context = self.get_trace(trace_id)
        if not context:
            return

        span = context.create_span(f"{service_name}_{method}_{endpoint}")
        span.set_tag("service_name", service_name)
        span.set_tag("endpoint", endpoint)
        span.set_tag("method", method)
        span.set_tag("status_code", status_code)
        span.finish("OK" if status_code < 400 else "ERROR")

    def log_database_query(
        self,
        trace_id: str,
        query_type: str,
        query_name: str,
        duration_ms: float,
    ) -> None:
        """Log a database query in the trace."""
        context = self.get_trace(trace_id)
        if not context:
            return

        span = context.create_span(f"db_{query_type}_{query_name}")
        span.set_tag("query_type", query_type)
        span.set_tag("query_name", query_name)
        span.set_tag("slow_query", duration_ms > 1000)
        span.finish()


# Global tracing manager
tracer = TracingManager()
