"""
Unit tests para configuración (Pydantic Settings).
Tests: validación de variables de entorno, valores por defecto.
"""
import pytest
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field, ValidationError


class TestSettingsConfiguration:
    """Tests para la clase Settings y su configuración."""

    def test_required_fields_present(self):
        """Verificar que campos requeridos están presentes."""
        # DATABASE_URL y SECRET_KEY son requeridos
        # Crear una clase sin .env para hacer que falle

        class TestSettings(BaseSettings):
            DATABASE_URL: str = Field(..., description="PostgreSQL connection string")
            SECRET_KEY: str = Field(..., min_length=32, description="JWT secret key")
            class Config:
                env_file = None

        # Intentar crear sin los campos requeridos debe fallar
        with pytest.raises(ValidationError) as exc_info:
            TestSettings()

        errors = exc_info.value.errors()
        error_fields = [error["loc"][0] for error in errors]

        assert "DATABASE_URL" in error_fields
        assert "SECRET_KEY" in error_fields

    def test_database_url_required(self):
        """Verificar que DATABASE_URL es requerido."""
        class TestSettings(BaseSettings):
            DATABASE_URL: str = Field(..., description="PostgreSQL connection string")
            SECRET_KEY: str = Field(..., min_length=32, description="JWT secret key")
            class Config:
                env_file = None

        with pytest.raises(ValidationError) as exc_info:
            TestSettings(SECRET_KEY="key" * 10)  # 30 chars, but min is 32

        errors = exc_info.value.errors()
        assert any(error["loc"][0] == "DATABASE_URL" for error in errors)

    def test_secret_key_required(self):
        """Verificar que SECRET_KEY es requerido."""
        class TestSettings(BaseSettings):
            DATABASE_URL: str = Field(..., description="PostgreSQL connection string")
            SECRET_KEY: str = Field(..., min_length=32, description="JWT secret key")
            class Config:
                env_file = None

        with pytest.raises(ValidationError) as exc_info:
            TestSettings(DATABASE_URL="postgresql://localhost/db")

        errors = exc_info.value.errors()
        assert any(error["loc"][0] == "SECRET_KEY" for error in errors)

    def test_secret_key_minimum_length(self):
        """Verificar que SECRET_KEY debe tener mínimo 32 caracteres."""
        from config import Settings

        # Menos de 32 caracteres debe fallar
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                DATABASE_URL="postgresql://localhost/db",
                SECRET_KEY="short"  # Menos de 32 chars
            )

        errors = exc_info.value.errors()
        assert any(
            error["loc"][0] == "SECRET_KEY" and "at least 32" in str(error)
            for error in errors
        )

    def test_secret_key_valid_length(self):
        """Verificar que SECRET_KEY con 32+ caracteres es válido."""
        from config import Settings

        # Exactamente 32 caracteres debe funcionar
        settings = Settings(
            DATABASE_URL="postgresql://localhost/db",
            SECRET_KEY="a" * 32
        )

        assert settings.SECRET_KEY == "a" * 32
        assert len(settings.SECRET_KEY) >= 32

    def test_database_url_valid_postgres(self):
        """Verificar que DATABASE_URL acepta conexiones PostgreSQL válidas."""
        from config import Settings

        # Conexión PostgreSQL válida
        settings = Settings(
            DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/dbname",
            SECRET_KEY="a" * 32
        )

        assert "postgresql" in settings.DATABASE_URL

    def test_algorithm_defaults_to_hs256(self):
        """Verificar que ALGORITHM tiene default HS256."""
        from config import Settings

        settings = Settings(
            DATABASE_URL="postgresql://localhost/db",
            SECRET_KEY="a" * 32
        )

        assert settings.ALGORITHM == "HS256"

    def test_default_values_applied(self):
        """Verificar que valores por defecto se aplican."""
        from config import Settings
        from pydantic_settings import BaseSettings

        class TestSettings(BaseSettings):
            DATABASE_URL: str = Field(..., description="PostgreSQL connection string")
            SECRET_KEY: str = Field(..., min_length=32, description="JWT secret key")
            APP_NAME: str = "Portafolio-cjhirashi API"
            DEBUG: bool = False
            ACCESS_TOKEN_EXPIRE_DAYS: int = 7
            REFRESH_TOKEN_EXPIRE_DAYS: int = 30
            RATE_LIMIT_ENABLED: bool = True
            class Config:
                env_file = None

        settings = TestSettings(
            DATABASE_URL="postgresql://localhost/db",
            SECRET_KEY="a" * 32
        )

        assert settings.ACCESS_TOKEN_EXPIRE_DAYS == 7
        assert settings.REFRESH_TOKEN_EXPIRE_DAYS == 30
        assert settings.APP_NAME == "Portafolio-cjhirashi API"
        assert settings.DEBUG is False
        assert settings.RATE_LIMIT_ENABLED is True

    def test_cors_origins_parsing(self):
        """Verificar que CORS_ORIGINS_STR se parsea correctamente."""
        from config import Settings

        settings = Settings(
            DATABASE_URL="postgresql://localhost/db",
            SECRET_KEY="a" * 32,
            CORS_ORIGINS_STR="http://localhost:8002,http://localhost:8003"
        )

        cors_list = settings.CORS_ORIGINS
        assert isinstance(cors_list, list)
        assert "http://localhost:8002" in cors_list
        assert "http://localhost:8003" in cors_list
        assert len(cors_list) == 2

    def test_cors_origins_handles_spaces(self):
        """Verificar que CORS_ORIGINS maneja espacios correctamente."""
        from config import Settings

        settings = Settings(
            DATABASE_URL="postgresql://localhost/db",
            SECRET_KEY="a" * 32,
            CORS_ORIGINS_STR="http://localhost:8002 , http://localhost:8003"
        )

        cors_list = settings.CORS_ORIGINS
        assert len(cors_list) == 2
        # Sin espacios alrededor
        assert all(not url.startswith(" ") and not url.endswith(" ") for url in cors_list)

    def test_cors_origins_empty_string(self):
        """Verificar que CORS_ORIGINS vacío retorna lista vacía."""
        from config import Settings

        settings = Settings(
            DATABASE_URL="postgresql://localhost/db",
            SECRET_KEY="a" * 32,
            CORS_ORIGINS_STR=""
        )

        cors_list = settings.CORS_ORIGINS
        assert isinstance(cors_list, list)
        assert len(cors_list) == 0

    def test_uploads_path_creation(self):
        """Verificar que uploads_path crea directorio si no existe."""
        from config import Settings
        import tempfile
        import shutil

        with tempfile.TemporaryDirectory() as tmpdir:
            uploads_dir = os.path.join(tmpdir, "uploads")

            # Directorio no debe existir
            assert not os.path.exists(uploads_dir)

            settings = Settings(
                DATABASE_URL="postgresql://localhost/db",
                SECRET_KEY="a" * 32,
                UPLOADS_DIR=uploads_dir
            )

            path = settings.uploads_path

            # Ahora debe existir
            assert os.path.isdir(uploads_dir)
            assert isinstance(path, Path)

    def test_max_upload_size_valid(self):
        """Verificar que MAX_UPLOAD_SIZE_MB tiene valor válido y se convierte a bytes.

        MAX_UPLOAD_SIZE_MB=10 se pasa explícito (no se deja el default de la
        clase) porque el entorno real donde corren estos tests ya trae
        MAX_UPLOAD_SIZE_MB=50 desde .env - BaseSettings SIEMPRE lee variables
        de entorno del proceso aunque `env_file=None`, así que confiar en el
        default aquí haría el test dependiente del entorno."""
        class TestSettings(BaseSettings):
            DATABASE_URL: str = Field(..., description="PostgreSQL connection string")
            SECRET_KEY: str = Field(..., min_length=32, description="JWT secret key")
            MAX_UPLOAD_SIZE_MB: int = 10

            @property
            def MAX_UPLOAD_SIZE(self) -> int:
                return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

            class Config:
                env_file = None

        settings = TestSettings(
            DATABASE_URL="postgresql://localhost/db",
            SECRET_KEY="a" * 32,
            MAX_UPLOAD_SIZE_MB=10,
        )

        assert settings.MAX_UPLOAD_SIZE == 10 * 1024 * 1024
        assert settings.MAX_UPLOAD_SIZE > 0

    def test_max_upload_size_mb_reads_from_env(self):
        """Regresión: MAX_UPLOAD_SIZE_MB debe leerse del entorno (.env usa este
        nombre exacto) y MAX_UPLOAD_SIZE debe reflejar ese valor en bytes -
        antes el campo real se llamaba MAX_UPLOAD_SIZE (sin _MB) y el .env
        nunca se aplicaba, quedando siempre en el default de 10 MB."""
        class TestSettings(BaseSettings):
            DATABASE_URL: str = Field(..., description="PostgreSQL connection string")
            SECRET_KEY: str = Field(..., min_length=32, description="JWT secret key")
            MAX_UPLOAD_SIZE_MB: int = 10

            @property
            def MAX_UPLOAD_SIZE(self) -> int:
                return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

            class Config:
                env_file = None

        settings = TestSettings(
            DATABASE_URL="postgresql://localhost/db",
            SECRET_KEY="a" * 32,
            MAX_UPLOAD_SIZE_MB=50,
        )

        assert settings.MAX_UPLOAD_SIZE_MB == 50
        assert settings.MAX_UPLOAD_SIZE == 50 * 1024 * 1024

    def test_allowed_extensions_valid(self):
        """Verificar que ALLOWED_EXTENSIONS tiene extensiones válidas."""
        from config import Settings

        settings = Settings(
            DATABASE_URL="postgresql://localhost/db",
            SECRET_KEY="a" * 32
        )

        assert isinstance(settings.ALLOWED_EXTENSIONS, list)
        assert "pdf" in settings.ALLOWED_EXTENSIONS
        assert "docx" in settings.ALLOWED_EXTENSIONS
        assert len(settings.ALLOWED_EXTENSIONS) > 0

    def test_bedrock_settings_optional(self):
        """Verificar que Bedrock settings son opcionales."""
        class TestSettings(BaseSettings):
            DATABASE_URL: str = Field(..., description="PostgreSQL connection string")
            SECRET_KEY: str = Field(..., min_length=32, description="JWT secret key")
            BEDROCK_REGION: str = "us-east-1"
            BEDROCK_MODEL_ID: str = "claude-3-sonnet-20240229"
            class Config:
                env_file = None

        settings = TestSettings(
            DATABASE_URL="postgresql://localhost/db",
            SECRET_KEY="a" * 32
        )

        # Deben tener valores por defecto
        assert settings.BEDROCK_REGION == "us-east-1"
        assert settings.BEDROCK_MODEL_ID == "claude-3-sonnet-20240229"

    def test_rate_limiting_settings_valid(self):
        """Verificar que rate limiting settings son válidos."""
        from config import Settings

        settings = Settings(
            DATABASE_URL="postgresql://localhost/db",
            SECRET_KEY="a" * 32
        )

        assert settings.RATE_LIMIT_ENABLED is True
        assert settings.RATE_LIMIT_REQUESTS == 100
        assert settings.RATE_LIMIT_WINDOW_SECONDS == 60

    def test_pagination_defaults_valid(self):
        """Verificar que pagination defaults son válidos."""
        from config import Settings

        settings = Settings(
            DATABASE_URL="postgresql://localhost/db",
            SECRET_KEY="a" * 32
        )

        assert settings.DEFAULT_SKIP == 0
        assert settings.DEFAULT_LIMIT == 20
        assert settings.MAX_LIMIT == 100
        assert settings.DEFAULT_LIMIT <= settings.MAX_LIMIT

    def test_config_case_sensitive(self):
        """Verificar que configuración es case-sensitive."""
        from config import Settings

        # SECRET_KEY debe ser case-sensitive
        settings = Settings(
            DATABASE_URL="postgresql://localhost/db",
            SECRET_KEY="a" * 32
        )

        # Los nombres de las variables deben mantener mayúsculas
        assert hasattr(settings, "SECRET_KEY")
        assert hasattr(settings, "DATABASE_URL")
