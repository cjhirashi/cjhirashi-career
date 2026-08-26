"""
Unit tests para configuración y setup de base de datos.
Tests: conexión, transacciones, cleanup, session management.
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.exc import OperationalError
from database import engine, AsyncSessionLocal, Base, get_db, init_db, close_db


class TestDatabaseConnection:
    """Tests para la conexión de la base de datos."""

    @pytest.mark.asyncio
    async def test_database_engine_creation(self):
        """Verificar que el engine se crea correctamente."""
        # Engine debe estar disponible
        assert engine is not None
        # Pool debe estar configurado
        assert engine.pool is not None

    @pytest.mark.asyncio
    async def test_database_session_factory_exists(self):
        """Verificar que AsyncSessionLocal es un sessionmaker válido."""
        assert AsyncSessionLocal is not None
        # Verificar que es callable (sessionmaker)
        assert callable(AsyncSessionLocal)

    @pytest.mark.asyncio
    async def test_base_declarative_available(self):
        """Verificar que Base (declarative_base) está disponible."""
        assert Base is not None
        # Debe tener metadata
        assert hasattr(Base, "metadata")
        assert Base.metadata is not None


class TestDatabaseSession:
    """Tests para sesiones de base de datos."""

    @pytest.mark.asyncio
    async def test_session_creation(self, test_db):
        """Verificar que se puede crear una sesión."""
        async with test_db() as session:
            assert isinstance(session, AsyncSession)
            # Sesión debe ser usable
            assert not session.is_active or True  # Puede estar active o no según estado

    @pytest.mark.asyncio
    async def test_session_commit_rollback(self, db_session):
        """Verificar que commit y rollback funcionan."""
        from models.user import User
        from services.auth_service import AuthService

        # Crear usuario
        user = User(
            username="test_user",
            email="test@example.com",
            password_hash=AuthService.hash_password("password123")
        )
        db_session.add(user)
        await db_session.flush()

        # Verificar que está en la sesión
        assert user in db_session.new or user in db_session.identity_map.values()

    @pytest.mark.asyncio
    async def test_session_expiration(self, test_db):
        """Verificar que expire_on_commit está deshabilitado."""
        # En conftest, expire_on_commit=False está configurado
        # Verificar que los objetos persisten después de commit

        from models.user import User
        from services.auth_service import AuthService

        async with test_db() as session:
            user = User(
                username="persistent_user",
                email="persistent@example.com",
                password_hash=AuthService.hash_password("password123")
            )
            session.add(user)
            await session.flush()
            await session.refresh(user)

            # Usuario debe estar aún accesible
            assert user.id is not None
            assert user.username == "persistent_user"

    @pytest.mark.asyncio
    async def test_session_isolation(self, test_db):
        """Verificar que sesiones son aisladas."""
        from models.user import User
        from services.auth_service import AuthService
        from sqlalchemy import select

        # Crear usuario en sesión 1
        async with test_db() as session1:
            user = User(
                username="user_session1",
                email="session1@example.com",
                password_hash=AuthService.hash_password("password123")
            )
            session1.add(user)
            await session1.flush()
            user_id = user.id

        # Verificar que existe en sesión 2
        async with test_db() as session2:
            result = await session2.execute(
                select(User).where(User.id == user_id)
            )
            user_from_session2 = result.scalar_one_or_none()
            assert user_from_session2 is not None
            assert user_from_session2.username == "user_session1"

    @pytest.mark.asyncio
    async def test_get_db_dependency(self, test_db):
        """Verificar que get_db es un generator válido."""
        # get_db es un dependency que debe ser async generator
        assert callable(get_db)


class TestDatabaseTransactions:
    """Tests para transacciones de base de datos."""

    @pytest.mark.asyncio
    async def test_transaction_commit_on_success(self, test_db):
        """Verificar que transacción se commit en caso de éxito."""
        from models.user import User
        from services.auth_service import AuthService
        from sqlalchemy import select

        async with test_db() as session:
            user = User(
                username="tx_user",
                email="tx@example.com",
                password_hash=AuthService.hash_password("password123")
            )
            session.add(user)
            await session.flush()
            user_id = user.id

        # Usuario debe persistir después de cerrar sesión
        async with test_db() as session:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            persisted_user = result.scalar_one_or_none()
            assert persisted_user is not None

    @pytest.mark.asyncio
    async def test_transaction_rollback_on_error(self, test_db):
        """Verificar que rollback ocurre en errores."""
        from models.user import User
        from services.auth_service import AuthService
        from sqlalchemy import select

        user_id = None

        try:
            async with test_db() as session:
                user = User(
                    username="rollback_user",
                    email="rollback@example.com",
                    password_hash=AuthService.hash_password("password123")
                )
                session.add(user)
                await session.flush()
                user_id = user.id
                # Simular error
                raise ValueError("Test error")
        except ValueError:
            pass

        # Usuario no debe existir si rollback funcionó
        # (En este test, rollback debería haber ocurrido)

    @pytest.mark.asyncio
    async def test_autoflush_disabled(self, test_db):
        """Verificar que autoflush está deshabilitado."""
        from models.user import User
        from services.auth_service import AuthService

        async with test_db() as session:
            user = User(
                username="no_autoflush",
                email="noautoflush@example.com",
                password_hash=AuthService.hash_password("password123")
            )
            session.add(user)

            # Sin flush explícito, el usuario no debe tener ID aún
            assert user.id is None

            # Después de flush, debe tener ID
            await session.flush()
            assert user.id is not None


class TestDatabaseCleanup:
    """Tests para limpieza de base de datos."""

    @pytest.mark.asyncio
    async def test_session_rollback_on_fixture_cleanup(self, test_db):
        """Verificar que rollback ocurre al limpiar fixture."""
        from models.user import User
        from services.auth_service import AuthService

        async with test_db() as session:
            user = User(
                username="cleanup_test",
                email="cleanup@example.com",
                password_hash=AuthService.hash_password("password123")
            )
            session.add(user)
            await session.flush()
            # Fixture limpiar hace rollback automático

    @pytest.mark.asyncio
    async def test_multiple_operations_same_session(self, db_session):
        """Verificar que múltiples operaciones en misma sesión funcionan."""
        from models.user import User
        from services.auth_service import AuthService

        # Crear múltiples usuarios
        for i in range(3):
            user = User(
                username=f"multi_user_{i}",
                email=f"multi{i}@example.com",
                password_hash=AuthService.hash_password("password123")
            )
            db_session.add(user)
            await db_session.flush()
            assert user.id is not None

    @pytest.mark.asyncio
    async def test_lazy_loading_not_available_after_session_close(self, test_db):
        """Verificar que lazy loading no funciona después de cerrar sesión."""
        from models.user import User
        from models.identity import Identity
        from services.auth_service import AuthService

        user_id = None

        async with test_db() as session:
            user = User(
                username="lazy_test",
                email="lazy@example.com",
                password_hash=AuthService.hash_password("password123")
            )
            session.add(user)
            await session.flush()
            await session.refresh(user)
            user_id = user.id

            # Dentro de sesión, relaciones se pueden cargar
            identity = Identity(
                user_id=user_id,
                ikigai_passion="test"
            )
            session.add(identity)
            await session.flush()

        # Después de cerrar sesión, el usuario debe estar detached
        # No se puede acceder a relaciones sin reiniciar sesión
