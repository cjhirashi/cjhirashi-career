"""
Unit tests para autenticación: JWT, password hashing, token management.
"""
import pytest
import jwt
from datetime import timedelta
from services.auth_service import AuthService
from config import settings


class TestPasswordHashing:
    """Tests para hashing y validación de contraseñas."""

    def test_hash_password(self):
        """Verificar que hash_password genera un hash."""
        password = "TestPassword123!"
        hashed = AuthService.hash_password(password)

        assert hashed is not None
        assert len(hashed) > 0
        assert hashed != password  # No es texto plano

    def test_verify_password_valid(self):
        """Verificar que verify_password funciona con contraseña correcta."""
        password = "TestPassword123!"
        hashed = AuthService.hash_password(password)

        assert AuthService.verify_password(password, hashed) is True

    def test_verify_password_invalid(self):
        """Verificar que verify_password falla con contraseña incorrecta."""
        password = "TestPassword123!"
        hashed = AuthService.hash_password(password)
        wrong_password = "WrongPassword!"

        assert AuthService.verify_password(wrong_password, hashed) is False

    def test_password_hash_consistency(self):
        """Verificar que hashes diferentes se generan para la misma contraseña."""
        password = "TestPassword123!"
        hash1 = AuthService.hash_password(password)
        hash2 = AuthService.hash_password(password)

        # Bcrypt genera salts diferentes, los hashes son diferentes
        assert hash1 != hash2
        # Pero ambos verifican correctamente
        assert AuthService.verify_password(password, hash1) is True
        assert AuthService.verify_password(password, hash2) is True


class TestJWTTokenCreation:
    """Tests para creación de JWT tokens."""

    def test_create_access_token(self):
        """Verificar que create_access_token crea un token válido."""
        data = {"sub": "1"}
        token, expires_in = AuthService.create_access_token(data)

        assert token is not None
        assert len(token) > 0
        assert expires_in > 0
        assert isinstance(token, str)

    def test_create_access_token_with_expiration(self):
        """Verificar que create_access_token respeta expires_delta."""
        data = {"sub": "1"}
        expires_delta = timedelta(hours=1)
        token, expires_in = AuthService.create_access_token(data, expires_delta)

        # expires_in debería ser aproximadamente 3600 segundos (1 hora)
        assert 3590 <= expires_in <= 3610

    def test_create_refresh_token(self):
        """Verificar que create_refresh_token crea un token válido."""
        data = {"sub": "1"}
        token, expires_in = AuthService.create_refresh_token(data)

        assert token is not None
        assert len(token) > 0
        assert expires_in > 0
        # El token debe tener el tipo "refresh"
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload.get("type") == "refresh"

    def test_access_token_payload(self):
        """Verificar que el access token contiene el payload correcto."""
        data = {"sub": "123"}
        token, _ = AuthService.create_access_token(data)

        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload.get("sub") == "123"
        assert "exp" in payload
        assert "iat" not in payload  # No debería incluir iat en access tokens


class TestJWTTokenDecoding:
    """Tests para decodificación de JWT tokens."""

    def test_decode_valid_access_token(self):
        """Verificar que decode_access_token decodifica un token válido."""
        data = {"sub": "1"}
        token, _ = AuthService.create_access_token(data)

        payload = AuthService.decode_access_token(token)
        assert payload.get("sub") == "1"

    def test_decode_invalid_token(self):
        """Verificar que decode_token falla con token inválido."""
        with pytest.raises(ValueError):
            AuthService.decode_token("invalid.token.here")

    def test_decode_expired_token(self):
        """Verificar que decode_token falla con token expirado."""
        data = {"sub": "1"}
        expires_delta = timedelta(seconds=-1)  # Expirado hace 1 segundo
        token, _ = AuthService.create_access_token(data, expires_delta)

        with pytest.raises(ValueError, match="expired"):
            AuthService.decode_token(token)

    def test_decode_refresh_token_as_access_token(self):
        """Verificar que no se puede usar refresh token como access token."""
        data = {"sub": "1"}
        refresh_token, _ = AuthService.create_refresh_token(data)

        with pytest.raises(ValueError, match="Invalid token type"):
            AuthService.decode_access_token(refresh_token)

    def test_decode_access_token_as_refresh_token(self):
        """Verificar que no se puede usar access token como refresh token."""
        data = {"sub": "1"}
        access_token, _ = AuthService.create_access_token(data)

        with pytest.raises(ValueError, match="Invalid token type"):
            AuthService.decode_refresh_token(access_token)


class TestExtractUserIdFromToken:
    """Tests para extraer user_id del token."""

    def test_extract_user_id_from_token(self):
        """Verificar que se puede extraer user_id de un token válido."""
        user_id = 42
        data = {"sub": str(user_id)}
        token, _ = AuthService.create_access_token(data)

        extracted_id = AuthService.extract_user_id_from_token(token)
        assert extracted_id == user_id

    def test_extract_user_id_from_invalid_token(self):
        """Verificar que falla al extraer user_id de token inválido."""
        with pytest.raises(ValueError):
            AuthService.extract_user_id_from_token("invalid.token")

    def test_extract_user_id_missing_in_token(self):
        """Verificar que falla si user_id no está en el token."""
        data = {"other": "value"}  # Sin "sub"
        token, _ = AuthService.create_access_token(data)

        with pytest.raises(ValueError, match="not found"):
            AuthService.extract_user_id_from_token(token)
