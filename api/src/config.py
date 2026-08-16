"""
Portafolio-cjhirashi API - Application Configuration
Loads environment variables and defines global configuration.
"""
from pydantic_settings import BaseSettings
from typing import List
from pathlib import Path


class Settings(BaseSettings):
    """Application configuration via environment variables."""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://mcpuser:mcppass123@postgres:5432/mcp_db"

    # JWT & Security
    SECRET_KEY: str = "portafolio-cjhirashi-secret-key-change-in-production-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 7
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

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
