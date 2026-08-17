"""
Authentication Service - JWT token management and password hashing.
Implements Single Responsibility Principle (authentication only).
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
import bcrypt
from config import settings

logger = logging.getLogger(__name__)


class AuthService:
    """
    Authentication service handling JWT creation, validation, and password operations.
    """

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt.

        Args:
            password: Plain text password to hash (max 72 bytes)

        Returns:
            Hashed password string
        """
        # Ensure password doesn't exceed bcrypt limit of 72 bytes
        if len(password.encode()) > 72:
            password = password[:72]

        # Hash password with bcrypt
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode(), salt)
        return hashed.decode()

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plain password against its hash.

        Args:
            plain_password: Plain text password to verify (max 72 bytes)
            hashed_password: Previously hashed password to compare against

        Returns:
            True if password matches, False otherwise
        """
        try:
            # Ensure password doesn't exceed bcrypt limit of 72 bytes
            if len(plain_password.encode()) > 72:
                plain_password = plain_password[:72]

            return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
        except Exception as e:
            logger.warning(f"Password verification failed: {e}")
            return False

    @staticmethod
    def _create_token(
        data: dict,
        token_type: str = "access",
        expires_delta: Optional[timedelta] = None
    ) -> tuple[str, int]:
        """
        Internal method to create JWT tokens (access or refresh).

        Implements DRY principle - centraliza la lógica común de creación de tokens.

        Args:
            data: Dictionary with data to encode in token
            token_type: Type of token ("access" or "refresh")
            expires_delta: Optional timedelta for token expiration

        Returns:
            Tuple of (token_string, expires_in_seconds)

        Raises:
            ValueError: If token creation fails
        """
        to_encode = data.copy()

        # Determine expiration based on token type
        if token_type == "refresh":
            expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS
        else:
            expire_days = settings.ACCESS_TOKEN_EXPIRE_DAYS

        # Calculate expiration time
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(days=expire_days)

        # Add expiration and type to token
        to_encode.update({"exp": expire})
        if token_type == "refresh":
            to_encode["type"] = "refresh"

        try:
            encoded_jwt = jwt.encode(
                to_encode,
                settings.SECRET_KEY,
                algorithm=settings.ALGORITHM
            )
            expires_in = (
                int(expires_delta.total_seconds())
                if expires_delta
                else (expire_days * 86400)
            )
            return encoded_jwt, expires_in
        except Exception as e:
            logger.error(f"Token creation failed ({token_type}): {e}")
            raise ValueError(f"Failed to create {token_type} token")

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> tuple[str, int]:
        """
        Create a JWT access token.

        Args:
            data: Dictionary with data to encode in token
            expires_delta: Optional timedelta for token expiration

        Returns:
            Tuple of (token_string, expires_in_seconds)

        Raises:
            ValueError: If token creation fails
        """
        return AuthService._create_token(data, "access", expires_delta)

    @staticmethod
    def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> tuple[str, int]:
        """
        Create a JWT refresh token.

        Args:
            data: Dictionary with data to encode in token
            expires_delta: Optional timedelta for token expiration

        Returns:
            Tuple of (token_string, expires_in_seconds)

        Raises:
            ValueError: If token creation fails
        """
        return AuthService._create_token(data, "refresh", expires_delta)

    @staticmethod
    def decode_token(token: str) -> dict:
        """
        Decode and validate a JWT token.

        Args:
            token: JWT token string to decode

        Returns:
            Dictionary with decoded token data

        Raises:
            ValueError: If token is invalid or expired
            jwt.ExpiredSignatureError: If token is expired
            jwt.InvalidTokenError: If token is malformed
        """
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            raise ValueError("Invalid token")

    @staticmethod
    def decode_access_token(token: str) -> dict:
        """
        Decode and validate an access token.

        Args:
            token: JWT access token to decode

        Returns:
            Dictionary with decoded token data

        Raises:
            ValueError: If token is invalid
        """
        payload = AuthService.decode_token(token)

        # Verify token type if present
        token_type = payload.get("type", "access")
        if token_type == "refresh":
            raise ValueError("Invalid token type")

        return payload

    @staticmethod
    def decode_refresh_token(token: str) -> dict:
        """
        Decode and validate a refresh token.

        Args:
            token: JWT refresh token to decode

        Returns:
            Dictionary with decoded token data

        Raises:
            ValueError: If token is invalid or not a refresh token
        """
        payload = AuthService.decode_token(token)

        # Verify token type
        token_type = payload.get("type")
        if token_type != "refresh":
            raise ValueError("Invalid token type")

        return payload

    @staticmethod
    def extract_user_id_from_token(token: str) -> int:
        """
        Extract user ID from token payload.

        Args:
            token: JWT token string

        Returns:
            User ID from token

        Raises:
            ValueError: If user_id not in token or token invalid
        """
        payload = AuthService.decode_access_token(token)
        user_id = payload.get("sub")

        if not user_id:
            raise ValueError("User ID not found in token")

        try:
            return int(user_id)
        except (ValueError, TypeError):
            raise ValueError("Invalid user ID in token")
