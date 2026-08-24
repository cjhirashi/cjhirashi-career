"""
Refresh Token Model - JWT token management for authentication.
"""
from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


from services.id_generator import register_id_listener


class RefreshToken(Base):
    """
    Refresh token storage for JWT token rotation.

    Implements secure token refresh strategy:
    - Each refresh token is single-use
    - Expired tokens are tracked
    - Enables token revocation
    """

    __tablename__ = "refresh_tokens"

    # Primary Key
    # --- Identificación (id prefijado + user_id para aislamiento) ---
    id = Column(String(20), primary_key=True, index=True)

    # Foreign Key
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Token Details
    # --- Campos de negocio ---
    token = Column(String(500), unique=True, nullable=False, index=True)
    token_hash = Column(String(255), nullable=False)  # Hashed version for comparison

    # Status
    is_revoked = Column(Boolean, default=False, nullable=False, index=True)
    is_used = Column(Boolean, default=False, nullable=False)

    # Expiration
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)

    # IP & Device Tracking (optional)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)

    # Timestamps
    # --- Auditoría temporal ---
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="refresh_tokens")

    def __repr__(self):
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, is_revoked={self.is_revoked})>"

register_id_listener(RefreshToken, "rtk")
