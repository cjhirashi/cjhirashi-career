"""
Enhanced Authentication Routes - Login, logout, refresh, register.
Uses AuthService for business logic.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta

from schemas.user import (
    LoginRequest, LoginResponse, UserResponse, UserCreate,
    TokenRefreshRequest, TokenRefreshResponse, LogoutResponse,
    PasswordChangeRequest, PasswordResetRequest
)
from models.user import User
from services.auth_service import AuthService
from repositories.user_repository import UserRepository
from middleware.auth import get_current_user
from database import get_db
from config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


async def get_user_repository(db: AsyncSession) -> UserRepository:
    """Dependency to get user repository."""
    return UserRepository(db)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user.

    Args:
        user_data: User registration data
        db: Database session

    Returns:
        Created user object

    Raises:
        HTTPException 400: If username or email already exists
    """
    repo = UserRepository(db)

    # Check if user already exists
    if await repo.user_exists(user_data.username, user_data.email):
        logger.warning(f"Registration failed - user exists: {user_data.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )

    # Create new user
    user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        phone=user_data.phone,
        country=user_data.country,
        professional_title=user_data.professional_title,
        password_hash=AuthService.hash_password(user_data.password),
        is_active=True
    )

    await repo.create(user)
    await repo.commit()

    logger.info(f"User registered: {user.username}")
    return user


@router.post("/login", response_model=LoginResponse)
async def login(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Login with username and password.

    Args:
        credentials: Login credentials
        db: Database session

    Returns:
        JWT tokens and user information

    Raises:
        HTTPException 401: If credentials are invalid
    """
    repo = UserRepository(db)

    # Find user
    user = await repo.get_by_username(credentials.username)

    # Validate credentials
    if not user or not AuthService.verify_password(credentials.password, user.password_hash):
        logger.warning(f"Login failed: {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Check if user is active
    if not user.is_active:
        logger.warning(f"Login failed - user inactive: {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # Update last login
    await repo.update_last_login(user.id)
    await repo.commit()
    await db.refresh(user)

    # Create tokens
    access_token, access_expires = AuthService.create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS)
    )

    refresh_token, refresh_expires = AuthService.create_refresh_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )

    logger.info(f"User logged in: {user.username}")

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=access_expires,
        user=UserResponse.from_orm(user)
    )


@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(
    request: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token.

    Args:
        request: Refresh token request
        db: Database session

    Returns:
        New access token

    Raises:
        HTTPException 401: If refresh token is invalid
    """
    try:
        payload = AuthService.decode_refresh_token(request.refresh_token)
        user_id = int(payload.get("sub"))
    except ValueError as e:
        logger.warning(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Verify user still exists and is active
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)

    if not user or not user.is_active:
        logger.warning(f"Token refresh failed - user invalid: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    # Create new access token
    access_token, expires_in = AuthService.create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS)
    )

    logger.info(f"Token refreshed for user: {user.username}")

    return TokenRefreshResponse(
        access_token=access_token,
        expires_in=expires_in
    )


@router.post("/logout", response_model=LogoutResponse)
async def logout():
    """
    Logout endpoint (client should delete token).

    Returns:
        Logout confirmation message
    """
    logger.info("User logout requested")
    return LogoutResponse(message="Logout successful. Please delete your token client-side.")


@router.post("/change-password")
async def change_password(
    request: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Change user password.

    Args:
        request: Password change request with current and new password
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException 400: If new password equals current password or current password is wrong
        HTTPException 401: If user is not authenticated
    """
    # Validar que nueva contraseña es diferente de la actual
    if request.current_password == request.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password"
        )

    # Verificar contraseña actual
    if not AuthService.verify_password(request.current_password, current_user.password_hash):
        logger.warning(f"Password change failed - wrong current password: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Actualizar contraseña
    current_user.password_hash = AuthService.hash_password(request.new_password)
    db.add(current_user)
    await db.commit()

    logger.info(f"Password changed for user: {current_user.id}")

    return {"message": "Password changed successfully"}
