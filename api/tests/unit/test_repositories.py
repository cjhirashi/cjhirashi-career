"""
Unit tests para repositories (data access layer).
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from models.user import User
from repositories.user_repository import UserRepository
from services.auth_service import AuthService


class TestUserRepository:
    """Tests para UserRepository."""

    @pytest.mark.asyncio
    async def test_create_user(self, db_session: AsyncSession, test_user_data: dict):
        """Verificar que se puede crear un usuario via repository."""
        repo = UserRepository(db_session)

        user = User(
            username=test_user_data["username"],
            email=test_user_data["email"],
            password_hash=AuthService.hash_password(test_user_data["password"]),
            full_name=test_user_data.get("full_name"),
            professional_title=test_user_data.get("professional_title")
        )

        created_user = await repo.create(user)
        assert created_user.id is not None
        assert created_user.username == test_user_data["username"]

    @pytest.mark.asyncio
    async def test_get_by_username(self, db_session: AsyncSession, test_user: User):
        """Verificar que se puede obtener usuario por username."""
        repo = UserRepository(db_session)
        db_session.add(test_user)
        await db_session.flush()

        user = await repo.get_by_username("testuser")
        assert user is not None
        assert user.username == "testuser"

    @pytest.mark.asyncio
    async def test_get_by_email(self, db_session: AsyncSession, test_user: User):
        """Verificar que se puede obtener usuario por email."""
        repo = UserRepository(db_session)
        db_session.add(test_user)
        await db_session.flush()

        user = await repo.get_by_email("test@example.com")
        assert user is not None
        assert user.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_by_id(self, db_session: AsyncSession, test_user: User):
        """Verificar que se puede obtener usuario por ID."""
        repo = UserRepository(db_session)
        db_session.add(test_user)
        await db_session.flush()

        user = await repo.get_by_id(test_user.id)
        assert user is not None
        assert user.id == test_user.id

    @pytest.mark.asyncio
    async def test_user_exists_true(self, db_session: AsyncSession, test_user: User):
        """Verificar que user_exists retorna True para usuario existente."""
        repo = UserRepository(db_session)
        db_session.add(test_user)
        await db_session.flush()

        exists = await repo.user_exists("testuser", "test@example.com")
        assert exists is True

    @pytest.mark.asyncio
    async def test_user_exists_false(self, db_session: AsyncSession):
        """Verificar que user_exists retorna False para usuario no existente."""
        repo = UserRepository(db_session)

        exists = await repo.user_exists("nonexistent", "notfound@example.com")
        assert exists is False

    @pytest.mark.asyncio
    async def test_update_last_login(self, db_session: AsyncSession, test_user: User):
        """Verificar que se puede actualizar last_login."""
        repo = UserRepository(db_session)
        db_session.add(test_user)
        await db_session.flush()

        assert test_user.last_login is None

        await repo.update_last_login(test_user.id)
        await db_session.refresh(test_user)

        assert test_user.last_login is not None

    @pytest.mark.asyncio
    async def test_repository_commit(self, db_session: AsyncSession):
        """Verificar que el repository puede hacer commit."""
        repo = UserRepository(db_session)

        # Crear usuario
        user = User(
            username="commituser",
            email="commit@example.com",
            password_hash=AuthService.hash_password("Password123!")
        )
        db_session.add(user)
        await db_session.flush()
        user_id = user.id

        # Commit
        await repo.commit()

        # Verificar que puede recuperarse
        retrieved = await repo.get_by_id(user_id)
        assert retrieved is not None

    @pytest.mark.asyncio
    async def test_repository_rollback(self, db_session: AsyncSession):
        """Verificar que el repository puede hacer rollback."""
        repo = UserRepository(db_session)

        # Crear usuario
        user = User(
            username="rollbackuser",
            email="rollback@example.com",
            password_hash=AuthService.hash_password("Password123!")
        )
        db_session.add(user)

        # Rollback
        await db_session.rollback()

        # Verificar que no se guardó
        check_user = await repo.get_by_username("rollbackuser")
        assert check_user is None
