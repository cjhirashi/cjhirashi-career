"""
Portafolio-cjhirashi API - Application Configuration
Loads environment variables and defines global configuration.
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Any, Dict, List
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
    MAX_UPLOAD_SIZE_MB: int = 10
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

    # AWS Bedrock — Harness local (Converse API) + Titan Embeddings + Titan Image.
    # Ver docs/BEDROCK-SYSTEM.md y ADR-008. BEDROCK_HARNESS_ARN es legacy AgentCore.
    BEDROCK_REGION: str = "us-east-1"
    BEDROCK_USE_LOCAL_HARNESS: bool = True
    BEDROCK_DEFAULT_MODEL_ID: str = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
    BEDROCK_ORCHESTRATOR_MODEL_ID: str = "us.amazon.nova-pro-v1:0"
    BEDROCK_IMAGE_MODEL_ID: str = "amazon.titan-image-generator-v2:0"
    BEDROCK_MAX_IMAGES_PER_DAY: int = 20
    BEDROCK_MAX_TOOL_RESULT_CHARS: int = 8000
    BEDROCK_HISTORY_WINDOW: int = 20
    BEDROCK_MAX_ROUND_TRIPS: int = 6
    BEDROCK_MAX_DELEGATIONS_PER_TURN: int = 3
    BEDROCK_DAILY_BUDGET_USD: float = 5.0
    BEDROCK_EMBEDDING_MODEL_ID: str = "amazon.titan-embed-text-v2:0"
    BEDROCK_HARNESS_ARN: str = ""
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""

    BEDROCK_AVAILABLE_MODELS: Dict[str, Dict[str, Any]] = {
        "amazon.nova-micro-v1:0": {
            "label": "Nova Micro",
            "tier": "economy",
            "price_input_per_million": 0.035,
            "price_output_per_million": 0.14,
        },
        "amazon.nova-lite-v1:0": {
            "label": "Nova Lite",
            "tier": "economy",
            "price_input_per_million": 0.06,
            "price_output_per_million": 0.24,
        },
        "deepseek.v3.2": {
            "label": "DeepSeek V3.2",
            "tier": "economy",
            "price_input_per_million": 0.62,
            "price_output_per_million": 1.85,
        },
        "cohere.command-r-v1:0": {
            "label": "Command R",
            "tier": "economy",
            "price_input_per_million": 0.15,
            "price_output_per_million": 0.60,
        },
        "us.anthropic.claude-haiku-4-5-20251001-v1:0": {
            "label": "Claude Haiku 4.5",
            "tier": "standard",
            "price_input_per_million": 1.00,
            "price_output_per_million": 5.00,
        },
        "us.amazon.nova-pro-v1:0": {
            "label": "Amazon Nova Pro",
            "tier": "standard",
            "price_input_per_million": 0.80,
            "price_output_per_million": 3.20,
        },
        "meta.llama3-3-70b-instruct-v1:0": {
            "label": "Llama 3.3 70B",
            "tier": "standard",
            "price_input_per_million": 0.72,
            "price_output_per_million": 0.72,
        },
        "mistral.mistral-large-2402-v1:0": {
            "label": "Mistral Large",
            "tier": "standard",
            "price_input_per_million": 2.00,
            "price_output_per_million": 6.00,
        },
        "us.amazon.nova-premier-v1:0": {
            "label": "Nova Premier",
            "tier": "premium",
            "price_input_per_million": 2.50,
            "price_output_per_million": 10.00,
        },
        "us.anthropic.claude-sonnet-4-5-20250929-v1:0": {
            "label": "Claude Sonnet 4.5",
            "tier": "premium",
            "price_input_per_million": 3.00,
            "price_output_per_million": 15.00,
        },
    }

    # Qdrant (Bedrock Chat's local knowledge base - operational_methodologies
    # + every career-domain record, kept in sync by CareerRepository)
    QDRANT_URL: str = "http://qdrant:6333"
    QDRANT_COLLECTION: str = "career_knowledge"

    # PDF Generator (renders a CVVersion's Markdown `content` into a PDF -
    # internal-only container, see routes/career_search.py's /pdf endpoint)
    PDF_GENERATOR_URL: str = "http://pdf_generator:8080"

    # LinkedIn OAuth (Share on LinkedIn + Sign In with LinkedIn using OpenID
    # Connect - both self-serve products, no LinkedIn app review required)
    LINKEDIN_CLIENT_ID: str = ""
    LINKEDIN_CLIENT_SECRET: str = ""
    LINKEDIN_REDIRECT_URI: str = ""
    LINKEDIN_FRONTEND_URL: str = ""

    # Job discovery (Indeed via Adzuna; other boards are public, no key)
    ADZUNA_APP_ID: str = ""
    ADZUNA_APP_KEY: str = ""
    ADZUNA_COUNTRY: str = "mx"
    JOB_DISCOVERY_TIMEOUT_SECONDS: float = 8.0
    JOB_DISCOVERY_MAX_RESULTS: int = 50
    JOB_DISCOVERY_USER_AGENT: str = "Portafolio-cjhirashi/1.0 (job-discovery; +https://cjhirashi.com)"

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
    def MAX_UPLOAD_SIZE(self) -> int:
        """Max upload size in bytes, derived from MAX_UPLOAD_SIZE_MB (.env)."""
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def uploads_path(self) -> Path:
        """Get uploads directory path."""
        path = Path(self.UPLOADS_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path


# Global settings instance
settings = Settings()
