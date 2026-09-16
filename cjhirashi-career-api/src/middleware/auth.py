"""
Middleware y dependencias de autenticación JWT.

- `get_current_user` — obligatorio; lanza 401 si el token es inválido
- `get_optional_current_user` — opcional; retorna None sin token
"""
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from models.user import User
from services.auth_service import AuthService
from database import get_db
from config import settings
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
    request: Request,
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

    # Dedicated agents must never become general-purpose API users. Their
    # approved surface is career data, Bedrock chat, and the unauthenticated
    # /public portal (the latter is handled without this dependency).
    if user.access_role == "agent":
        career_path = request.url.path.startswith("/career/")
        bedrock_chat = request.url.path == "/bedrock/chat" and request.method == "POST"
        if not career_path and not bedrock_chat:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Agent token is not authorized for this endpoint",
            )

        # Agents operate on the portfolio owner's records. An explicit owner_id
        # in the JWT takes precedence; otherwise fall back to the configured
        # portfolio owner so tokens without the claim remain valid.
        owner_id = payload.get("owner_id") or settings.PUBLIC_PORTAL_USER_ID
        owner_result = await db.execute(
            select(User).where(User.id == str(owner_id))
        )
        owner = owner_result.scalar_one_or_none()
        if owner is None or not owner.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Assigned owner not found or inactive",
            )
        return owner

    return user


async def get_optional_current_user(
    request: Request,
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
        return await get_current_user(request, credentials, db)
    except HTTPException:
        return None
