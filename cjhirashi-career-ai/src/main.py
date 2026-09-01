"""
FastAPI application for cjhirashi-career-ai microservice (FASE 3-6).

Extracted from monolith:
- services/bedrock/ (24 modules) — agent logic, Bedrock integration
- routes/bedrock.py (32 endpoints) — chat, agent management, usage metrics
- routes/bedrock_tasks.py (3 endpoints) — task execution

Architecture:
- Receives SSE chat requests from Orchestrator (via Gateway)
- Calls Orchestrator API for career CRUD (via HTTP internal)
- Manages agent execution, usage tracking, delegation
- FASE 5: Rate limiting middleware protects all endpoints
- FASE 6: Structured logging + distributed tracing for observability
"""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import sys

from config import settings
from middleware.rate_limit import rate_limit_middleware
from middleware.logging_config import setup_logging
from middleware.request_logging import RequestLoggingMiddleware

# ============================================================================
# Logging Setup (FASE 6 — Structured JSON Logging)
# ============================================================================
# Setup structured JSON logging
setup_logging(level="DEBUG" if settings.DEBUG else "INFO")
logger = logging.getLogger(__name__)


# ============================================================================
# Lifecycle Management
# ============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle for startup/shutdown."""
    # Startup
    logger.info("Starting up IA service...")
    # TODO: Initialize Bedrock client, Qdrant connection, etc.

    yield

    # Shutdown
    logger.info("Shutting down IA service...")
    # TODO: Close connections


# ============================================================================
# FastAPI Application
# ============================================================================
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Bedrock Agent & IA service (extracted from monolith in FASE 3-5)",
    lifespan=lifespan,
)

# ============================================================================
# Middleware (FASE 5-6 - Rate Limiting + Request Logging)
# ============================================================================
# Request logging middleware (innermost - logs everything)
app.add_middleware(RequestLoggingMiddleware)

# Rate limiting middleware
app.middleware("http")(rate_limit_middleware)


# ============================================================================
# Health Check
# ============================================================================
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for load balancers."""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with service info."""
    return {
        "message": "cjhirashi-career IA Service",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
    }


# ============================================================================
# Router Imports (FASE 3-6)
# ============================================================================
# Import routers and register them
try:
    from routes import bedrock, bedrock_tasks, metrics, prometheus, observability
    app.include_router(bedrock.router, prefix="/api")
    app.include_router(bedrock_tasks.router, prefix="/api")
    app.include_router(metrics.router, prefix="/api")
    app.include_router(prometheus.router, prefix="/api")
    app.include_router(observability.router, prefix="/api")
    logger.info("All routers registered: bedrock, tasks, metrics, prometheus, observability")
except ImportError as e:
    logger.warning(f"Failed to import routers: {e}. Continue without them.")


# ============================================================================
# Global Exception Handler (Placeholder)
# ============================================================================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions."""
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8010,
        reload=settings.DEBUG,
    )
