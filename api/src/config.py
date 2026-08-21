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

    # AWS Bedrock (Optional) - chat model + embeddings for the Bedrock Chat
    # assistant's knowledge base (Qdrant). Static IAM keys, not an instance
    # role: this runs on a VPS, not on AWS compute.
    BEDROCK_REGION: str = "us-east-1"
    # "us." prefix = cross-region inference profile, required for this model
    # (on-demand invocation by the bare model id is rejected by Bedrock -
    # confirmed against the real profile definition, which fans out to
    # us-east-1/us-east-2/us-west-2; the IAM policy must allow InvokeModel/
    # Converse on the profile ARN AND on the foundation-model ARN in all 3
    # of those regions, not just BEDROCK_REGION).
    BEDROCK_EMBEDDING_MODEL_ID: str = "amazon.titan-embed-text-v2:0"
    # ARN of the AgentCore Harness resource the chat model runs on (see
    # docs/09-DECISIONS - Bedrock uses Harness, not a hand-rolled Converse
    # loop). The chat model itself is NOT read from BEDROCK_MODEL_ID above -
    # it's whatever model is currently configured on this harness, switchable
    # at runtime via POST /bedrock/model (see services/bedrock_service.py).
    BEDROCK_HARNESS_ARN: str = ""
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""

    # Models the harness is allowed to switch to from the app. Each entry's
    # IAM access (and, for Anthropic models, AWS Marketplace Foundation Model
    # Agreement) must already be provisioned on the harness execution role
    # before it's listed here - adding a model is an infrastructure change,
    # not a runtime toggle. Prices are official Bedrock on-demand USD rates
    # per million tokens, confirmed 2026-08-21 (not estimates).
    BEDROCK_AVAILABLE_MODELS: Dict[str, Dict[str, Any]] = {
        "us.anthropic.claude-sonnet-4-5-20250929-v1:0": {
            "label": "Claude Sonnet 4.5",
            "price_input_per_million": 3.00,
            "price_output_per_million": 15.00,
        },
        "us.anthropic.claude-haiku-4-5-20251001-v1:0": {
            "label": "Claude Haiku 4.5",
            "price_input_per_million": 1.00,
            "price_output_per_million": 5.00,
        },
        "us.amazon.nova-pro-v1:0": {
            "label": "Amazon Nova Pro",
            "price_input_per_million": 0.80,
            "price_output_per_million": 3.20,
        },
        "deepseek.v3.2": {
            "label": "DeepSeek V3.2",
            "price_input_per_million": 0.62,
            "price_output_per_million": 1.85,
        },
    }

    # Qdrant (Bedrock Chat's local knowledge base - operational_methodologies
    # + every career-domain record, kept in sync by CareerRepository)
    QDRANT_URL: str = "http://qdrant:6333"
    QDRANT_COLLECTION: str = "career_knowledge"

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
