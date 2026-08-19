"""
Portafolio-cjhirashi API - Application Configuration
Loads environment variables and defines global configuration.
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
from pathlib import Path


class Settings(BaseSettings):
    """Application configuration via environment variables."""

    # Database (REQUIRED - no defaults for production safety)
    DATABASE_URL: str = Field(
        ...,
        description="PostgreSQL connection string (required)"
    )

    # JWT & Security (REQUIRED - no defaults for production safety)
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

    # CORS Origins (as string, parsed to list)
    CORS_ORIGINS_STR: str = "http://localhost:8002,http://localhost:8003,http://localhost:8004"

    # Application
    APP_NAME: str = "Portafolio-cjhirashi API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # File Uploads
    UPLOADS_DIR: str = "/app/uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10 MB
    ALLOWED_EXTENSIONS: List[str] = ["pdf", "doc", "docx", "jpg", "jpeg", "png", "gif"]

    # MinIO (object storage bucket - required)
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

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # Pagination
    DEFAULT_SKIP: int = 0
    DEFAULT_LIMIT: int = 20
    MAX_LIMIT: int = 100

    # AWS Bedrock (Optional)
    BEDROCK_REGION: str = "us-east-1"
    BEDROCK_MODEL_ID: str = "claude-3-sonnet-20240229"

    # LinkedIn OAuth (Share on LinkedIn + Sign In with LinkedIn using OpenID
    # Connect - both self-serve products, no LinkedIn app review required)
    LINKEDIN_CLIENT_ID: str = ""
    LINKEDIN_CLIENT_SECRET: str = ""
    LINKEDIN_REDIRECT_URI: str = ""
    LINKEDIN_FRONTEND_URL: str = ""

    # Public Portal - this is a single-owner portfolio, so the unauthenticated
    # /public/* routes (routes/public.py) always serve this one user's data.
    PUBLIC_PORTAL_USER_ID: int = 2

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def CORS_ORIGINS(self) -> List[str]:
        """Parse CORS_ORIGINS_STR to list of allowed origins."""
        return [
            url.strip()
            for url in self.CORS_ORIGINS_STR.replace(",", " ").split()
            if url.strip()
        ]

    @property
    def uploads_path(self) -> Path:
        """Get uploads directory path."""
        path = Path(self.UPLOADS_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path


# Global settings instance
settings = Settings()
