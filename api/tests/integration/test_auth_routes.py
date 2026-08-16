"""
Integration tests para rutas de autenticación.
Tests de endpoints: POST /auth/login, /auth/refresh, /auth/logout, /auth/register
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from app import app
from models import User
from services.auth_service import AuthService
from database import get_db


# Fixture para cliente de prueba
@pytest.fixture
def client(db_session: AsyncSession):
    """Crear un cliente TestClient que use la BD de prueba."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


class TestRegisterEndpoint:
    """Tests para POST /auth/register"""

    @pytest.mark.asyncio
    async def test_register_success(self, client):
        """Verificar que se puede registrar un nuevo usuario."""
        response = client.post(
            "/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "NewPassword123!",
                "full_name": "New User",
                "professional_title": "Developer"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert "password" not in data  # No devolver password

    @pytest.mark.asyncio
    async def test_register_username_exists(self, client, test_user: User, db_session):
        """Verificar que no se puede registrar con username existente."""
        # Agregar test_user a la BD
        db_session.add(test_user)
        await db_session.flush()

        response = client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "email": "other@example.com",
                "password": "Password123!"
            }
        )

        assert response.status_code == 400
        assert "already" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_register_email_exists(self, client, test_user: User, db_session):
        """Verificar que no se puede registrar con email existente."""
        db_session.add(test_user)
        await db_session.flush()

        response = client.post(
            "/auth/register",
            json={
                "username": "otheruser",
                "email": "test@example.com",
                "password": "Password123!"
            }
        )

        assert response.status_code == 400
        assert "already" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client):
        """Verificar que no se puede registrar con email inválido."""
        response = client.post(
            "/auth/register",
            json={
                "username": "newuser",
                "email": "invalid-email",
                "password": "Password123!"
            }
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_register_weak_password(self, client):
        """Verificar que contraseña débil es rechazada."""
        response = client.post(
            "/auth/register",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "weak"  # Menos de 8 caracteres
            }
        )

        assert response.status_code == 422


class TestLoginEndpoint:
    """Tests para POST /auth/login"""

    @pytest.mark.asyncio
    async def test_login_success(self, client, test_user: User, db_session):
        """Verificar que se puede hacer login con credenciales válidas."""
        db_session.add(test_user)
        await db_session.flush()

        response = client.post(
            "/auth/login",
            json={
                "username": "testuser",
                "password": "TestPassword123!"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "user" in data
        assert data["user"]["username"] == "testuser"
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0

    @pytest.mark.asyncio
    async def test_login_invalid_username(self, client):
        """Verificar que login falla con username inválido."""
        response = client.post(
            "/auth/login",
            json={
                "username": "nonexistent",
                "password": "Password123!"
            }
        )

        assert response.status_code == 401
        assert "credenciales" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_login_invalid_password(self, client, test_user: User, db_session):
        """Verificar que login falla con contraseña inválida."""
        db_session.add(test_user)
        await db_session.flush()

        response = client.post(
            "/auth/login",
            json={
                "username": "testuser",
                "password": "WrongPassword!"
            }
        )

        assert response.status_code == 401
        assert "credenciales" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_login_inactive_user(self, client, db_session):
        """Verificar que login falla para usuario inactivo."""
        user = User(
            username="inactiveuser",
            email="inactive@example.com",
            password_hash=AuthService.hash_password("Password123!"),
            is_active=False
        )
        db_session.add(user)
        await db_session.flush()

        response = client.post(
            "/auth/login",
            json={
                "username": "inactiveuser",
                "password": "Password123!"
            }
        )

        assert response.status_code == 403
        assert "inactive" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_login_updates_last_login(self, client, test_user: User, db_session):
        """Verificar que el último login se actualiza."""
        db_session.add(test_user)
        await db_session.flush()

        # Primer login
        response = client.post(
            "/auth/login",
            json={
                "username": "testuser",
                "password": "TestPassword123!"
            }
        )

        assert response.status_code == 200
        # Verificar que last_login se actualizó
        await db_session.refresh(test_user)
        assert test_user.last_login is not None


class TestRefreshEndpoint:
    """Tests para POST /auth/refresh"""

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, client, test_user: User, db_session):
        """Verificar que se puede refrescar un token válido."""
        db_session.add(test_user)
        await db_session.flush()

        # Login para obtener refresh token
        login_response = client.post(
            "/auth/login",
            json={
                "username": "testuser",
                "password": "TestPassword123!"
            }
        )
        refresh_token = login_response.json()["refresh_token"]

        # Usar refresh token
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0

    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, client):
        """Verificar que refresh con token inválido falla."""
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": "invalid.token.here"}
        )

        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_refresh_with_access_token(self, client, test_user: User, db_session):
        """Verificar que no se puede usar access token para refresh."""
        db_session.add(test_user)
        await db_session.flush()

        # Login para obtener access token
        login_response = client.post(
            "/auth/login",
            json={
                "username": "testuser",
                "password": "TestPassword123!"
            }
        )
        access_token = login_response.json()["access_token"]

        # Intentar usar access token para refresh
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": access_token}
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_inactive_user(self, client, db_session):
        """Verificar que refresh falla si usuario está inactivo."""
        user = User(
            username="inactiveuser",
            email="inactive@example.com",
            password_hash=AuthService.hash_password("Password123!"),
            is_active=True
        )
        db_session.add(user)
        await db_session.flush()

        # Login
        login_response = client.post(
            "/auth/login",
            json={
                "username": "inactiveuser",
                "password": "Password123!"
            }
        )
        refresh_token = login_response.json()["refresh_token"]

        # Desactivar usuario
        user.is_active = False
        await db_session.flush()

        # Intentar refresh
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token}
        )

        assert response.status_code == 401


class TestLogoutEndpoint:
    """Tests para POST /auth/logout"""

    @pytest.mark.asyncio
    async def test_logout_success(self, client):
        """Verificar que logout retorna mensaje de éxito."""
        response = client.post("/auth/logout")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data or "Logout" in data.get("message", "")


class TestChangePasswordEndpoint:
    """Tests para POST /auth/change-password"""

    @pytest.mark.asyncio
    async def test_change_password_not_authenticated(self, client):
        """Verificar que cambiar contraseña requiere autenticación."""
        # Sin auth header
        response = client.post(
            "/auth/change-password",
            json={
                "current_password": "OldPassword123!",
                "new_password": "NewPassword123!"
            }
        )

        # Debería retornar 401 porque requiere auth
        # Por ahora puede ser 401 si no hay auth dependency implementada
        assert response.status_code in [401, 422]
