"""
Configuration for cjhirashi-career-ai microservice.

Loads variables from .env and environment, similar to main API but focused
on Bedrock-specific configuration.
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Any, Dict


class Settings(BaseSettings):
    """Configuration for the IA service."""

    # =========================================================================
    # Service Metadata
    # =========================================================================
    APP_NAME: str = "cjhirashi-career IA"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # =========================================================================
    # Database (for usage logging and conversation history)
    # =========================================================================
    DATABASE_URL: str = Field(
        ...,
        description="PostgreSQL connection string (required)"
    )

    # =========================================================================
    # JWT & Security
    # =========================================================================
    SECRET_KEY: str = Field(
        ...,
        min_length=32,
        description="JWT secret key (minimum 32 characters, required)"
    )
    ALGORITHM: str = Field(default="HS256", description="JWT algorithm")

    # =========================================================================
    # AWS Bedrock — Converse API, embeddings, image generation
    # =========================================================================
    BEDROCK_REGION: str = "us-east-1"
    BEDROCK_USE_CONVERSE_STREAM: bool = False
    BEDROCK_DEFAULT_MODEL_ID: str = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
    BEDROCK_ORCHESTRATOR_MODEL_ID: str = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
    BEDROCK_IMAGE_MODEL_ID: str = "amazon.titan-image-generator-v2:0"
    BEDROCK_EMBEDDING_MODEL_ID: str = "amazon.titan-embed-text-v2:0"

    # Limits
    BEDROCK_MAX_IMAGES_PER_DAY: int = 20
    BEDROCK_MAX_TOOL_RESULT_CHARS: int = 8000
    BEDROCK_MAX_DELEGATIONS_PER_TURN: int = 3
    BEDROCK_HISTORY_WINDOW: int = 20
    BEDROCK_MAX_ROUND_TRIPS: int = 6

    # Prompt caching (ADR-019)
    BEDROCK_PROMPT_CACHE_ENABLED: bool = True

    # Budget control (USD, checked daily)
    BEDROCK_DAILY_BUDGET_USD: float = 5.0

    # AWS credentials (REQUIRED)
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""

    # Available models (same as main API for consistency)
    BEDROCK_AVAILABLE_MODELS: Dict[str, Dict[str, Any]] = {
        "amazon.nova-lite-v1:0": {
            "label": "Nova Lite",
            "tier": "economy",
            "invoke_via": "foundation",
            "price_input_per_million": 0.06,
            "price_output_per_million": 0.24,
        },
        "deepseek.v3.2": {
            "label": "DeepSeek V3.2",
            "tier": "economy",
            "invoke_via": "foundation",
            "price_input_per_million": 0.62,
            "price_output_per_million": 1.85,
        },
        "us.anthropic.claude-haiku-4-5-20251001-v1:0": {
            "label": "Claude Haiku 4.5",
            "tier": "standard",
            "invoke_via": "inference_profile",
            "price_input_per_million": 1.00,
            "price_output_per_million": 5.00,
            "supports_prompt_cache": True,
        },
        "mistral.mistral-large-2402-v1:0": {
            "label": "Mistral Large",
            "tier": "standard",
            "invoke_via": "foundation",
            "price_input_per_million": 2.00,
            "price_output_per_million": 6.00,
        },
        "us.anthropic.claude-sonnet-4-5-20250929-v1:0": {
            "label": "Claude Sonnet 4.5",
            "tier": "premium",
            "invoke_via": "inference_profile",
            "price_input_per_million": 3.00,
            "price_output_per_million": 15.00,
            "supports_prompt_cache": True,
        },
    }

    # =========================================================================
    # Qdrant — Vector knowledge base for agent
    # =========================================================================
    QDRANT_URL: str = "http://qdrant:6333"
    QDRANT_COLLECTION: str = "career_knowledge"

    # =========================================================================
    # Orchestrator API — for career CRUD operations
    # =========================================================================
    ORCHESTRATOR_API_BASE_URL: str = "http://api:8001"
    ORCHESTRATOR_API_TIMEOUT_SECONDS: float = 30

    # =========================================================================
    # MinIO — for file uploads referenced in tools
    # =========================================================================
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ROOT_USER: str = ""
    MINIO_ROOT_PASSWORD: str = ""
    MINIO_BUCKET: str = "cjhirashi-career"
    MINIO_PUBLIC_URL: str = ""

    # =========================================================================
    # Pydantic Settings
    # =========================================================================
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


# Singleton
settings = Settings()
