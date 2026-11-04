"""
PortalSite Model - A measured website within the analytics system.
Stores the domain, public key for ingestion, owner token hash, and configuration.
"""
from sqlalchemy import Column, DateTime, ForeignKey, String, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from database import Base
from services.id_generator import register_id_listener


class PortalSite(Base):
    """One website being measured: domain, ingestion key, owner token, timezone."""

    __tablename__ = "portal_sites"

    # --- Identificación ---
    id = Column(String(20), primary_key=True, index=True)
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # --- Configuración ---
    name = Column(String(255), nullable=False)
    domain = Column(String(255), nullable=False, unique=True, index=True)
    public_key = Column(String(24), nullable=False, unique=True, index=True)
    owner_token_hash = Column(String(64), nullable=False)  # SHA-256 hex
    allowed_hosts = Column(JSONB, nullable=False, server_default="[]")
    timezone = Column(String(50), nullable=False, server_default="America/Mexico_City")
    active = Column(Boolean, nullable=False, server_default="true", default=True)

    # --- Auditoría temporal ---
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    def __repr__(self):
        return f"<PortalSite(id={self.id}, domain='{self.domain}')>"


register_id_listener(PortalSite, "psi")
