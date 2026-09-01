"""
FastAPI application for cjhirashi-career-ai microservice (FASE 3).

Extracted from monolith:
- services/bedrock/ (24 modules) — agent logic, Bedrock integration
- routes/bedrock.py (32 endpoints) — chat, agent management, usage metrics
- routes/bedrock_tasks.py (3 endpoints) — task execution

Architecture:
- Receives SSE chat requests from Orchestrator (via Gateway in FASE 5)
- Calls Orchestrator API for career CRUD (via HTTP internal)
- Manages agent execution, usage tracking, delegation
"""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import sys

from config import settings

# ============================================================================
# Logging Setup
# ============================================================================
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
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
    description="Bedrock Agent & IA service (extracted from monolith in FASE 3)",
    lifespan=lifespan,
)


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
# TODO: Router Imports (FASE 3 continuation)
# ============================================================================
# These will be implemented as we move bedrock.py and bedrock_tasks.py:
#
# from routes import bedrock, bedrock_tasks
# app.include_router(bedrock.router, prefix="/api")
# app.include_router(bedrock_tasks.router, prefix="/api")


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
