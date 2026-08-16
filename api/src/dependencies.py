"""
Dependency injection configuration para FastAPI.
Centraliza la creación de dependencias reutilizables.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from repositories.user_repository import UserRepository
from middleware.auth import get_current_user
from models.user import User


# ============================================================================
# REPOSITORY DEPENDENCIES
# ============================================================================

async def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    """
    Dependency para obtener UserRepository.

    Usado en endpoints que necesitan acceso a operaciones de usuario.

    Args:
        db: Sesión de base de datos (inyectada por FastAPI)

    Returns:
        Instancia de UserRepository
    """
    return UserRepository(db)


# ============================================================================
# AUTH DEPENDENCIES (Re-exported para conveniencia)
# ============================================================================

async def get_current_user_dependency(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency que verifica autenticación y retorna usuario actual.

    Alias para middleware.auth.get_current_user - centraliza su uso.

    Args:
        current_user: Usuario autenticado del middleware

    Returns:
        Usuario actual autenticado

    Raises:
        HTTPException 401: Si no está autenticado
    """
    return current_user
