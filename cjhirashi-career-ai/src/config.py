"""
cjhirashi-career-ai - configuración de la aplicación.

Carga variables de entorno vía pydantic-settings y expone el singleton `settings`.
Las variables obligatorias no tienen valor por defecto: si falta una, el arranque falla
con un error de validación que nombra la variable (RF-006).
"""
import re

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


_ALLOWED_JWT_ALGORITHMS = frozenset({"HS256", "HS384", "HS512"})


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

    # Cliente REST (RF-003): timeout por petición y tope duro de registros que `list` lee (coste/latencia).
    API_TIMEOUT_SECONDS: float = Field(default=15.0, gt=0)
    API_LIST_MAX_ITEMS: int = Field(default=500, ge=1)

    # Memoria del agente (full-text, D-24).
    MEMORY_FTS_CONFIG: str = Field(default="spanish_unaccent", description="Configuración regconfig de FTS (D-29: ignora tildes)")

    @field_validator("ALGORITHM")
    @classmethod
    def _validate_algorithm(cls, value: str) -> str:
        # Lista cerrada: evita `none` y la confusión de algoritmo (HMAC vs asimétricos).
        if value not in _ALLOWED_JWT_ALGORITHMS:
            raise ValueError(f"ALGORITHM debe ser uno de {sorted(_ALLOWED_JWT_ALGORITHMS)}")
        return value

    @field_validator("MEMORY_FTS_CONFIG")
    @classmethod
    def _validate_fts_config(cls, value: str) -> str:
        # Se interpola en DDL (columna generada): solo identificadores simples.
        if not re.fullmatch(r"[a-z_]+", value):
            raise ValueError("MEMORY_FTS_CONFIG debe cumplir [a-z_]+ (p. ej. 'spanish_unaccent')")
        return value

    # Proveedor de modelos Bedrock (spec 009 RF-005). Mismos nombres y valores que la API.
    BEDROCK_REGION: str = "us-east-1"
    BEDROCK_USE_CONVERSE_STREAM: bool = False
    # Stable Image Core (ADR-010/ADR-025) solo está disponible en us-west-2; región aparte de Converse.
    BEDROCK_IMAGE_REGION: str = "us-west-2"
    BEDROCK_IMAGE_MODEL_ID: str = "stability.stable-image-core-v1:1"
    # Kill-switch global de cachePoint (ADR-019); solo aplica a modelos con soporte en el catálogo.
    BEDROCK_PROMPT_CACHE_ENABLED: bool = True
    # Runtime del agente: mismos valores por defecto que cjhirashi-career-api/src/config.py (95-96, 121-128).
    BEDROCK_DEFAULT_MODEL_ID: str = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
    BEDROCK_ORCHESTRATOR_MODEL_ID: str = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
    BEDROCK_MAX_OUTPUT_TOKENS: int = Field(default=8192, ge=1)
    BEDROCK_HISTORY_WINDOW: int = Field(default=20, ge=1)
    BEDROCK_MAX_ROUND_TRIPS: int = Field(default=6, ge=1)
    BEDROCK_DAILY_BUDGET_USD: float = Field(default=5.0, ge=0)
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
