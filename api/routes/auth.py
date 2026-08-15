"""
Rutas de autenticación: login, logout, registro.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from schemas.user import LoginRequest, TokenResponse, UserCreate, UserResponse
from models.user import User
from utils.security import verify_password, create_access_token, hash_password
from database import get_db
from config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint de login con username y password.

    Args:
        credentials: Username y password
        db: Sesión de base de datos

    Returns:
        Token JWT y datos del usuario

    Raises:
        HTTPException 401: Si las credenciales son inválidas
    """
    # Buscar usuario por username
    result = await db.execute(
        select(User).where(User.username == credentials.username)
    )
    user = result.scalar_one_or_none()

    # Validar credenciales
    if user is None or not verify_password(credentials.password, user.password_hash):
        logger.warning(f"Login failed for username: {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Crear token JWT
    access_token = create_access_token(data={"sub": user.username})

    logger.info(f"User logged in: {user.username}")

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,  # En segundos
        user=UserResponse.model_validate(user)
    )


@router.post("/logout")
async def logout():
    """
    Endpoint de logout.
    Nota: Con JWT stateless, el logout es manejado por el cliente
    eliminando el token. Este endpoint es principalmente informativo.

    Returns:
        Mensaje de confirmación
    """
    return {"message": "Logout exitoso. Elimina el token del cliente."}


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint de registro de nuevo usuario.

    Args:
        user_data: Datos del nuevo usuario
        db: Sesión de base de datos

    Returns:
        Usuario creado

    Raises:
        HTTPException 400: Si el username o email ya existen
    """
    # Verificar si el username ya existe
    result = await db.execute(
        select(User).where(User.username == user_data.username)
    )
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El username ya está en uso"
        )

    # Verificar si el email ya existe
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está en uso"
        )

    # Crear nuevo usuario
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password(user_data.password)
    )

    db.add(new_user)
    await db.flush()
    await db.refresh(new_user)

    logger.info(f"New user registered: {new_user.username}")

    return UserResponse.model_validate(new_user)
