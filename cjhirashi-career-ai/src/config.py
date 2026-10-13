"""
cjhirashi-career-ai - configuración de la aplicación.

Carga variables de entorno vía pydantic-settings y expone el singleton `settings`.
Las variables obligatorias no tienen valor por defecto: si falta una, el arranque falla
con un error de validación que nombra la variable (RF-006).
"""
import re

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración global leída desde `.env` y variables de entorno."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # BD propia del harness (career_ai_db). Nunca career_db.
    AI_DATABASE_URL: str = Field(..., description="PostgreSQL (asyncpg) del harness")

    # JWT compartido con la API (mismo .env): el harness solo valida, no emite.
    SECRET_KEY: str = Field(..., min_length=32, description="Secreto JWT compartido (mín. 32)")
    ALGORITHM: str = Field(..., description="Algoritmo JWT compartido con la API")

    # Frontera de salida hacia la API de datos.
    API_BASE_URL: str = Field(..., description="URL base de la API de datos")
    AI_SERVICE_TOKEN: str = Field(..., description="JWT de la cuenta de servicio del harness")

    # Memoria del agente (full-text, D-24).
    MEMORY_FTS_CONFIG: str = Field(default="spanish", description="Configuración regconfig de FTS")

    @field_validator("MEMORY_FTS_CONFIG")
    @classmethod
    def _validate_fts_config(cls, value: str) -> str:
        # Se interpola en DDL (columna generada): solo identificadores simples.
        if not re.fullmatch(r"[a-z_]+", value):
            raise ValueError("MEMORY_FTS_CONFIG debe cumplir [a-z_]+ (p. ej. 'spanish')")
        return value

    # Proveedor de modelos Bedrock (spec 009 RF-005). Mismos nombres y valores que la API.
    BEDROCK_REGION: str = "us-east-1"
    BEDROCK_USE_CONVERSE_STREAM: bool = False
    # Stable Image Core (ADR-010/ADR-025) solo está disponible en us-west-2; región aparte de Converse.
    BEDROCK_IMAGE_REGION: str = "us-west-2"
    BEDROCK_IMAGE_MODEL_ID: str = "stability.stable-image-core-v1:1"
    # Kill-switch global de cachePoint (ADR-019); solo aplica a modelos con soporte en el catálogo.
    BEDROCK_PROMPT_CACHE_ENABLED: bool = True
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""

    APP_NAME: str = "cjhirashi-career-ai"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False


settings = Settings()


_provider = None


def get_provider():
    """Fábrica del `ModelProvider` (una instancia por proceso). Único sitio fuera de
    `providers/bedrock/` que importa la implementación Bedrock (RF-005, test AST de frontera)."""
    global _provider
    if _provider is None:
        from providers.bedrock.converse import BedrockProvider

        _provider = BedrockProvider(settings)
    return _provider
