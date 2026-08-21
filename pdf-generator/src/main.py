"""Main FastAPI application for PDF Generator."""

import logging
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from src.config import settings
from src.routes import generate

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="PDF generation service for CVs and Cover Letters",
)


# Include routes
app.include_router(generate.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": settings.app_name,
            "version": settings.app_version,
        },
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return JSONResponse(
        status_code=200,
        content={
            "message": f"Welcome to {settings.app_name}",
            "version": settings.app_version,
            "endpoints": {
                "health": "/health",
                "generate_cv": "POST /generate/cv",
                "generate_cover_letter": "POST /generate/cover-letter",
                "generate_markdown_document": "POST /generate/markdown-document",
            },
        },
    )


@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle ValueError exceptions."""
    logger.error(f"ValueError: {str(exc)}")
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8080,
        reload=settings.debug,
    )
