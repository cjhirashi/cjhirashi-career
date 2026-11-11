"""
cjhirashi-career API - Application Configuration.

Carga variables de entorno vía pydantic-settings y expone un singleton
`settings` usado en toda la aplicación (BD, JWT, Bedrock, MinIO, etc.).
"""
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import Any, Dict, List
from pathlib import Path


class Settings(BaseSettings):
    """Configuración global leída desde `.env` y variables de entorno."""

    # -------------------------------------------------------------------------
    # Base de datos (obligatorio en producción)
    # -------------------------------------------------------------------------
    DATABASE_URL: str = Field(
        ...,
        description="PostgreSQL connection string (required)"
    )

    # -------------------------------------------------------------------------
    # JWT y seguridad (SECRET_KEY obligatorio, mín. 32 caracteres)
    # -------------------------------------------------------------------------
    SECRET_KEY: str = Field(
        ...,
        min_length=32,
        description="JWT secret key (minimum 32 characters, required)"
    )
    ALGORITHM: str = Field(
        default="HS256",
        description="JWT algorithm"
    )
    ACCESS_TOKEN_EXPIRE_DAYS: int = Field(
        default=7,
        description="Access token expiration in days"
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=30,
        description="Refresh token expiration in days"
    )

    # -------------------------------------------------------------------------
    # CORS y metadatos de la aplicación
    # -------------------------------------------------------------------------
    CORS_ORIGINS_STR: str = "http://localhost:8002,http://localhost:8003"

    # Application
    APP_NAME: str = "cjhirashi-career API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # -------------------------------------------------------------------------
    # Subida de archivos (límites locales; almacenamiento real en MinIO)
    # -------------------------------------------------------------------------
    UPLOADS_DIR: str = "/app/uploads"
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: List[str] = ["pdf", "doc", "docx", "jpg", "jpeg", "png", "gif"]

    # -------------------------------------------------------------------------
    # MinIO — bucket S3-compatible para archivos públicos/privados
    # -------------------------------------------------------------------------
    MINIO_ENDPOINT: str = Field(
        ...,
        description="MinIO host:port on the internal Docker network (required)"
    )
    MINIO_ROOT_USER: str = Field(..., description="MinIO access key (required)")
    MINIO_ROOT_PASSWORD: str = Field(..., description="MinIO secret key (required)")
    MINIO_BUCKET: str = Field(..., description="Bucket name for uploaded files (required)")
    MINIO_PUBLIC_URL: str = Field(
        ...,
        description="Public base URL the bucket is exposed at (e.g. https://files.cjhirashi.com), required"
    )

    # -------------------------------------------------------------------------
    # Rate limiting y paginación por defecto en listados CRUD
    # -------------------------------------------------------------------------
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # Pagination
    DEFAULT_SKIP: int = 0
    DEFAULT_LIMIT: int = 20
    MAX_LIMIT: int = 100

    # -------------------------------------------------------------------------
    # Job discovery — agregadores externos (Adzuna, boards públicos, etc.)
    # -------------------------------------------------------------------------
    ADZUNA_APP_ID: str = ""
    ADZUNA_APP_KEY: str = ""
    ADZUNA_COUNTRY: str = "mx"
    JOB_DISCOVERY_TIMEOUT_SECONDS: float = 8.0
    JOB_DISCOVERY_MAX_RESULTS: int = 50
    JOB_DISCOVERY_USER_AGENT: str = "cjhirashi-career/1.0 (job-discovery; +https://cjhirashi.com)"

    # -------------------------------------------------------------------------
    # GitHub — PAT de solo lectura para el L3 agent_github
    # -------------------------------------------------------------------------
    GITHUB_TOKEN: str = ""

    # -------------------------------------------------------------------------
    # Consulta web — Brave Search opcional; si vacío se usa DuckDuckGo
    # -------------------------------------------------------------------------
    BRAVE_SEARCH_API_KEY: str = ""

    # -------------------------------------------------------------------------
    # Portal público — usuario único cuyos datos sirve /public/*
    # user_id es VARCHAR prefijado (usr-2), no un entero. Un valor numérico
    # legado (PUBLIC_PORTAL_USER_ID=2) se normaliza a usr-2.
    # -------------------------------------------------------------------------
    PUBLIC_PORTAL_USER_ID: str = "usr-2"

    @field_validator("PUBLIC_PORTAL_USER_ID", mode="before")
    @classmethod
    def coerce_legacy_numeric_portal_user_id(cls, value: Any) -> Any:
        if value is None or value == "":
            return value
        if isinstance(value, int) or (isinstance(value, str) and value.strip().isdigit()):
            return f"usr-{int(value)}"
        return str(value).strip()

    # -------------------------------------------------------------------------
    # Pydantic Settings — carga desde .env
    # -------------------------------------------------------------------------
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

    # -------------------------------------------------------------------------
    # Propiedades derivadas (no vienen del .env directamente)
    # -------------------------------------------------------------------------
    @property
    def CORS_ORIGINS(self) -> List[str]:
        """Parse CORS_ORIGINS_STR to list of allowed origins."""
        return [
            url.strip()
            for url in self.CORS_ORIGINS_STR.replace(",", " ").split()
            if url.strip()
        ]

    @property
    def MAX_UPLOAD_SIZE(self) -> int:
        """Max upload size in bytes, derived from MAX_UPLOAD_SIZE_MB (.env)."""
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def uploads_path(self) -> Path:
        """Get uploads directory path."""
        path = Path(self.UPLOADS_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path


# Singleton global — importar como `from config import settings`
settings = Settings()
