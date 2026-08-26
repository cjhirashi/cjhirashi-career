"""
Punto de entrada de la aplicación FastAPI.

Responsabilidades:
- Lifecycle (startup/shutdown): BD, MinIO, scheduler LinkedIn y tareas de agentes
- Middleware CORS y manejadores globales de errores
- Registro de todos los routers (auth, career, bedrock, public, …)
- Endpoints de sistema: /health, /
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import asyncio
import logging
import sys

from config import settings
from database import init_db, close_db
from routes import auth_enhanced
from routes import career_identity, career_search, career_digital, career_support, career_metrics, career_methodologies, job_discovery
from routes import bedrock
from routes import bedrock_tasks
from routes import admin_sections
from routes import pdf_templates, pdf_template_styles
from routes import files
from routes import linkedin
from routes import public
from routes import notifications
from services import storage_service, linkedin_scheduler, task_scheduler

# ============================================================================
# Logging
# ============================================================================
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


# ============================================================================
# Lifecycle — startup y shutdown de recursos compartidos
# ============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager para inicializar y cerrar recursos.
    Se ejecuta al inicio y al cierre de la aplicación.
    """
    # Startup
    logger.info("Starting up API server...")
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

    try:
        storage_service.ensure_bucket()
        logger.info("MinIO bucket ready")
    except Exception as e:
        # Files/uploads will fail until MinIO is reachable, but the rest of
        # the API (career CRUD, PDF templates, auth, Bedrock) must stay up.
        # A hard raise here used to crash uvicorn on a bad MINIO_ENDPOINT,
        # which Cloudflare surfaces as error 520 on every /api request.
        logger.error(
            "Failed to initialize MinIO bucket (%s). File storage is unavailable; other routes will still serve.",
            e,
        )

    linkedin_task = asyncio.create_task(linkedin_scheduler.scheduler_loop())
    agent_task_loop = asyncio.create_task(task_scheduler.scheduler_loop())
    logger.info("LinkedIn post scheduler started")
    logger.info("Agent task scheduler started")

    yield

    # Shutdown
    logger.info("Shutting down API server...")
    linkedin_task.cancel()
    agent_task_loop.cancel()
    await close_db()


# ============================================================================
# Instancia FastAPI
# ============================================================================
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API REST para gestión de documentos con autenticación JWT",
    lifespan=lifespan
)


# ============================================================================
# Middleware CORS
# ============================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Manejadores globales de excepciones
# ============================================================================
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Maneja errores de validación de Pydantic con respuesta personalizada."""
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Error de validación",
            "errors": exc.errors()
        }
    )


# Manejador global de excepciones
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Maneja excepciones no capturadas."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Error interno del servidor"
        }
    )


# ============================================================================
# Endpoints de sistema (sin prefijo de dominio)
# ============================================================================
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Endpoint de health check para monitoreo.
    Retorna el estado de la API.
    """
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Endpoint raíz con información de la API."""
    return {
        "message": "MCP Tools API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health"
    }


# ============================================================================
# Routers — un módulo por dominio funcional
# ============================================================================
app.include_router(auth_enhanced.router)
app.include_router(career_identity.router)
app.include_router(career_search.router)
app.include_router(job_discovery.router)
app.include_router(career_digital.router)
app.include_router(career_support.router)
app.include_router(career_metrics.router)
app.include_router(career_methodologies.router)
app.include_router(bedrock.router)
app.include_router(bedrock_tasks.router)
app.include_router(notifications.router)
app.include_router(admin_sections.router)
app.include_router(pdf_templates.router)
app.include_router(pdf_template_styles.router)
app.include_router(files.router)
app.include_router(linkedin.router)
app.include_router(public.router)


# ============================================================================
# Log de arranque (import-time, antes del primer request)
# ============================================================================
logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION} initialized")
logger.info(f"CORS enabled for origins: {settings.CORS_ORIGINS}")
