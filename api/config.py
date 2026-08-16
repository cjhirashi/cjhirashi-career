"""
Configuración de la aplicación API.
Carga variables de entorno y define configuración global.
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Configuración de la aplicación mediante variables de entorno."""

    # Base de datos
    DATABASE_URL: str = "postgresql+asyncpg://user:password@postgres:5432/mcp_db"

    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production-min-32-chars-recommended"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 7

    # CORS (como string, parseado manualmente)
    CORS_ORIGINS_STR: str = "http://localhost:8003 http://mcp_frontend:8000 http://localhost:3000"

    # App
    APP_NAME: str = "MCP Tools API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def CORS_ORIGINS(self) -> List[str]:
        """Parsea CORS_ORIGINS_STR a lista."""
        return [url.strip() for url in self.CORS_ORIGINS_STR.replace(",", " ").split() if url.strip()]


# Instancia global de configuración
settings = Settings()
