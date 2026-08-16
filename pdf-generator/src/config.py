"""Configuration for PDF Generator service."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Application
    app_name: str = "PDF Generator"
    app_version: str = "1.0.0"
    debug: bool = False

    # PDF Generation
    pdf_timeout_seconds: int = 30
    max_pdf_size_mb: int = 50

    # Logging
    log_level: str = "INFO"

    class Config:
        """Pydantic config."""

        env_file = ".env"
        case_sensitive = False


settings = Settings()
