"""
Middleware y dependencias de autenticación JWT.

- `get_current_user` — obligatorio; lanza 401 si el token es inválido
- `get_optional_current_user` — opcional; retorna None sin token
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from models.user import User
from services.auth_service import AuthService
from database import get_db
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# Security scheme — extrae Bearer token del header Authorization
# ============================================================================
security = HTTPBearer()


# ============================================================================
# Dependencias de autenticación
# ============================================================================
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency para obtener el usuario actual desde el token JWT.

    Args:
        credentials: Credenciales Bearer del header Authorization
        db: Sesión de base de datos

    Returns:
        Usuario autenticado

    Raises:
        HTTPException: Si el token es inválido o el usuario no existe
    """
    token = credentials.credentials

    # Decodificar y validar token
    try:
        payload = AuthService.decode_access_token(token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Obtener user_id del payload (sub contiene el ID del usuario)
    user_id_str: Optional[str] = payload.get("sub")
    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido: falta información de usuario",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user_id = user_id_str

    # Buscar usuario por ID (búsqueda por primary key es más eficiente)
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado o inactivo",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return user


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Dependency para obtener el usuario actual de forma opcional.
    Si no hay token, retorna None en lugar de error.

    Args:
        credentials: Credenciales Bearer opcionales
        db: Sesión de base de datos

    Returns:
        Usuario autenticado o None
    """
    if credentials is None:
        return None

    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None
