"""
Punto de entrada de la aplicación FastAPI.
Configura middleware, CORS, rutas y lifecycle events.
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
from routes import career_identity, career_search, career_digital, career_support, career_metrics, career_methodologies
from routes import files
from routes import linkedin
from routes import public
from services import storage_service, linkedin_scheduler

# Configurar logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


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
        logger.error(f"Failed to initialize MinIO bucket: {e}")
        raise

    scheduler_task = asyncio.create_task(linkedin_scheduler.scheduler_loop())
    logger.info("LinkedIn post scheduler started")

    yield

    # Shutdown
    logger.info("Shutting down API server...")
    scheduler_task.cancel()
    await close_db()


# Crear instancia de FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API REST para gestión de documentos con autenticación JWT",
    lifespan=lifespan
)


# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Manejador global de errores de validación
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


# Health check endpoint
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


# Incluir routers
app.include_router(auth_enhanced.router)
app.include_router(career_identity.router)
app.include_router(career_search.router)
app.include_router(career_digital.router)
app.include_router(career_support.router)
app.include_router(career_metrics.router)
app.include_router(career_methodologies.router)
app.include_router(files.router)
app.include_router(linkedin.router)
app.include_router(public.router)


# Log de startup
logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION} initialized")
logger.info(f"CORS enabled for origins: {settings.CORS_ORIGINS}")
