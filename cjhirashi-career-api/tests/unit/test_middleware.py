"""
Unit tests para middleware de autenticación JWT.
Tests: validación de tokens, user isolation, error handling.
"""
import pytest
from fastapi import HTTPException, status
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.security import HTTPAuthorizationCredentials

from middleware.auth import get_current_user, get_optional_current_user
from models.user import User
from services.auth_service import AuthService


class TestGetCurrentUser:
    """Tests para dependency get_current_user."""

    @pytest.mark.asyncio
    async def test_valid_jwt_returns_user(self, db_session, test_user: User):
        """Verificar que JWT válido retorna el usuario."""
        # Crear token válido
        token, _ = AuthService.create_access_token(
            data={"sub": str(test_user.id)}
        )

        # Crear mock de credenciales
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        # Agregar usuario a BD
        db_session.add(test_user)
        await db_session.flush()

        # Llamar a get_current_user
        user = await get_current_user(credentials, db_session)

        assert user is not None
        assert user.id == test_user.id
        assert user.username == test_user.username

    @pytest.mark.asyncio
    async def test_expired_jwt_raises_401(self, db_session, test_user: User):
        """Verificar que JWT expirado lanza 401."""
        # Crear token expirado
        token, _ = AuthService.create_access_token(
            data={"sub": str(test_user.id)},
            expires_delta=timedelta(seconds=-1)
        )

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        # Debe lanzar HTTPException con status 401
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, db_session)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "expired" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_invalid_jwt_raises_401(self, db_session):
        """Verificar que JWT inválido lanza 401."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid.token.format"
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, db_session)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_missing_user_id_in_token_raises_401(self, db_session):
        """Verificar que token sin user ID lanza 401."""
        # Crear token sin "sub"
        token, _ = AuthService.create_access_token(data={"other": "value"})

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, db_session)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "usuario" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_user_id_malformed_raises_401(self, db_session):
        """Verificar que user ID malformado lanza 401."""
        # Crear token con user_id no numérico
        token, _ = AuthService.create_access_token(
            data={"sub": "not-a-number"}
        )

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, db_session)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "malformado" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_nonexistent_user_raises_401(self, db_session):
        """Verificar que usuario no existente lanza 401."""
        # Crear token para usuario que no existe
        token, _ = AuthService.create_access_token(
            data={"sub": "99999"}  # ID que no existe
        )

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, db_session)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "no encontrado" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_inactive_user_raises_401(self, db_session):
        """Verificar que usuario inactivo lanza 401."""
        # Crear usuario inactivo
        user = User(
            username="inactive",
            email="inactive@example.com",
            password_hash=AuthService.hash_password("password123"),
            is_active=False
        )
        db_session.add(user)
        await db_session.flush()
        await db_session.refresh(user)

        # Token válido pero usuario está inactivo
        token, _ = AuthService.create_access_token(
            data={"sub": str(user.id)}
        )

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, db_session)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "inactivo" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_user_isolation_read_only_own_data(self, db_session, test_user: User):
        """Verificar que usuario solo ve sus datos (row-level security)."""
        # Crear dos usuarios
        user1 = User(
            username="user1",
            email="user1@example.com",
            password_hash=AuthService.hash_password("password123")
        )
        user2 = User(
            username="user2",
            email="user2@example.com",
            password_hash=AuthService.hash_password("password123")
        )
        db_session.add(user1)
        db_session.add(user2)
        await db_session.flush()
        await db_session.refresh(user1)
        await db_session.refresh(user2)

        # Token para user1
        token, _ = AuthService.create_access_token(
            data={"sub": str(user1.id)}
        )
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        # get_current_user debería retornar user1
        current_user = await get_current_user(credentials, db_session)

        assert current_user.id == user1.id
        assert current_user.id != user2.id

    @pytest.mark.asyncio
    async def test_jwt_header_validation(self, db_session, test_user: User):
        """Verificar que header Authorization se valida correctamente."""
        token, _ = AuthService.create_access_token(
            data={"sub": str(test_user.id)}
        )
        db_session.add(test_user)
        await db_session.flush()

        # Scheme debe ser "Bearer"
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        user = await get_current_user(credentials, db_session)
        assert user.id == test_user.id


class TestGetOptionalCurrentUser:
    """Tests para dependency get_optional_current_user."""

    @pytest.mark.asyncio
    async def test_no_credentials_returns_none(self, db_session):
        """Verificar que sin credenciales retorna None."""
        user = await get_optional_current_user(credentials=None, db=db_session)

        assert user is None

    @pytest.mark.asyncio
    async def test_valid_credentials_returns_user(self, db_session, test_user: User):
        """Verificar que credenciales válidas retornan usuario."""
        token, _ = AuthService.create_access_token(
            data={"sub": str(test_user.id)}
        )
        db_session.add(test_user)
        await db_session.flush()
        await db_session.refresh(test_user)

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        user = await get_optional_current_user(credentials=credentials, db=db_session)

        assert user is not None
        assert user.id == test_user.id

    @pytest.mark.asyncio
    async def test_invalid_credentials_returns_none(self, db_session):
        """Verificar que credenciales inválidas retornan None."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid.token"
        )

        user = await get_optional_current_user(credentials=credentials, db=db_session)

        assert user is None

    @pytest.mark.asyncio
    async def test_expired_token_returns_none(self, db_session):
        """Verificar que token expirado retorna None."""
        token, _ = AuthService.create_access_token(
            data={"sub": "1"},
            expires_delta=timedelta(seconds=-1)
        )

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        user = await get_optional_current_user(credentials=credentials, db=db_session)

        assert user is None
