"""Tests for logging and tracing (FASE 6)."""

import pytest
import logging
from unittest.mock import Mock, patch

from middleware.logging_config import RequestLogger, PerformanceLogger
from middleware.tracing import TracingManager, Span


class TestRequestLogger:
    """Test cases for request logger."""

    def test_get_correlation_id(self):
        """Test correlation ID generation."""
        logger = RequestLogger()

        id1 = logger.get_correlation_id()
        id2 = logger.get_correlation_id()

        assert id1 != id2
        assert len(id1) == 36  # UUID format

    def test_log_request(self, caplog):
        """Test logging HTTP request."""
        logger = RequestLogger()

        with caplog.at_level(logging.INFO):
            logger.log_request(
                method="POST",
                path="/api/bedrock/chat",
                correlation_id="test-id-123",
                user_id="usr-1",
                client_ip="192.168.1.1",
            )

        assert "HTTP_REQUEST_RECEIVED" in caplog.text

    def test_log_response(self, caplog):
        """Test logging HTTP response."""
        logger = RequestLogger()

        with caplog.at_level(logging.INFO):
            logger.log_response(
                correlation_id="test-id-123",
                status_code=200,
                response_time_ms=45.5,
                response_size=1024,
            )

        assert "HTTP_RESPONSE_SENT" in caplog.text

    def test_log_error(self, caplog):
        """Test logging error."""
        logger = RequestLogger()

        with caplog.at_level(logging.ERROR):
            logger.log_error(
                correlation_id="test-id-123",
                error_type="ValueError",
                error_message="Invalid request",
            )

        assert "HTTP_ERROR" in caplog.text


class TestPerformanceLogger:
    """Test cases for performance logger."""

    def test_log_database_query(self, caplog):
        """Test logging database query."""
        logger = PerformanceLogger()

        with caplog.at_level(logging.INFO):
            logger.log_database_query(
                query_type="SELECT",
                query_name="get_user",
                duration_ms=250,
                correlation_id="test-id-123",
            )

        assert "DATABASE_QUERY" in caplog.text

    def test_log_external_api_call(self, caplog):
        """Test logging external API call."""
        logger = PerformanceLogger()

        with caplog.at_level(logging.INFO):
            logger.log_external_api_call(
                service_name="orchestrator",
                endpoint="/conversations",
                method="GET",
                status_code=200,
                duration_ms=450,
                correlation_id="test-id-123",
            )

        assert "EXTERNAL_API_CALL" in caplog.text

    def test_log_rate_limit_check(self, caplog):
        """Test logging rate limit check."""
        logger = PerformanceLogger()

        with caplog.at_level(logging.INFO):
            logger.log_rate_limit_check(
                client_id="user-123",
                limiter_name="chat",
                allowed=True,
                remaining=29,
                check_time_ms=2.5,
                correlation_id="test-id-123",
            )

        assert "RATE_LIMIT_CHECK" in caplog.text


class TestSpan:
    """Test cases for tracing spans."""

    def test_create_span(self):
        """Test creating a span."""
        span = Span(
            trace_id="trace-1",
            span_id="span-1",
            parent_span_id=None,
            operation_name="test_op",
            start_time=1000.0,
        )

        assert span.trace_id == "trace-1"
        assert span.span_id == "span-1"
        assert span.operation_name == "test_op"

    def test_set_tag(self):
        """Test adding tags to span."""
        span = Span(
            trace_id="trace-1",
            span_id="span-1",
            parent_span_id=None,
            operation_name="test_op",
            start_time=1000.0,
        )

        span.set_tag("user_id", "usr-123")
        span.set_tag("status_code", 200)

        assert span.tags["user_id"] == "usr-123"
        assert span.tags["status_code"] == 200

    def test_finish_span(self):
        """Test finishing a span."""
        span = Span(
            trace_id="trace-1",
            span_id="span-1",
            parent_span_id=None,
            operation_name="test_op",
            start_time=1000.0,
        )

        span.finish("OK")

        assert span.status == "OK"
        assert span.end_time is not None

    def test_duration_ms(self):
        """Test span duration calculation."""
        span = Span(
            trace_id="trace-1",
            span_id="span-1",
            parent_span_id=None,
            operation_name="test_op",
            start_time=1000.0,
        )

        span.end_time = 1000.5
        assert span.duration_ms == 500  # 0.5 seconds = 500ms


class TestTracingContext:
    """Test cases for tracing context."""

    def test_create_trace(self):
        """Test creating a tracing context."""
        manager = TracingManager()

        trace_id = manager.create_trace()

        assert trace_id
        assert trace_id in manager.active_traces

    def test_create_span_in_trace(self):
        """Test creating spans in a trace."""
        manager = TracingManager()
        trace_id = manager.create_trace()

        context = manager.get_trace(trace_id)
        span = context.create_span("test_op")

        assert span.trace_id == trace_id
        assert len(context.get_spans()) == 1

    def test_end_trace(self):
        """Test ending a trace."""
        manager = TracingManager()
        trace_id = manager.create_trace()

        trace_data = manager.end_trace(trace_id)

        assert trace_data["trace_id"] == trace_id
        assert trace_id not in manager.active_traces

    def test_log_external_call(self):
        """Test logging external call in trace."""
        manager = TracingManager()
        trace_id = manager.create_trace()

        manager.log_external_call(
            trace_id=trace_id,
            service_name="orchestrator",
            endpoint="/conversations",
            method="GET",
            duration_ms=250,
            status_code=200,
        )

        context = manager.get_trace(trace_id)
        assert len(context.get_spans()) > 1  # Root + external call

    def test_log_database_query(self):
        """Test logging database query in trace."""
        manager = TracingManager()
        trace_id = manager.create_trace()

        manager.log_database_query(
            trace_id=trace_id,
            query_type="SELECT",
            query_name="get_user",
            duration_ms=150,
        )

        context = manager.get_trace(trace_id)
        assert len(context.get_spans()) > 1  # Root + query
