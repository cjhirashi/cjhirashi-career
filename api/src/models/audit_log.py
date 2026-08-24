"""
Audit Log Model - System audit trail and compliance logging.
"""
from sqlalchemy import Column, Integer, ForeignKey, String, Text, DateTime, Enum, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
import enum


class AuditAction(str, enum.Enum):
    """Type of auditable action."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    EXPORT = "export"
    IMPORT = "import"
    SHARE = "share"
    DOWNLOAD = "download"
    GRANT_PERMISSION = "grant_permission"
    REVOKE_PERMISSION = "revoke_permission"


class AuditLog(Base):
    """
    Audit trail for compliance and security.

    Supports:
    - Complete audit trail of user actions
    - Admin visibility and compliance
    - Security investigation
    - Data integrity verification
    """

    __tablename__ = "audit_logs"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Foreign Key
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Audit Details
    action = Column(Enum(AuditAction), nullable=False, index=True)
    resource_type = Column(String(100), nullable=False, index=True)  # User, Competency, Evidence, etc.
    resource_id = Column(String(100), nullable=True)
    resource_name = Column(String(255), nullable=True)

    # Change Details
    change_description = Column(Text, nullable=True)
    old_values = Column(JSON, nullable=True)  # Previous values
    new_values = Column(JSON, nullable=True)  # New values

    # Request Context
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    request_path = Column(String(500), nullable=True)
    request_method = Column(String(10), nullable=True)

    # Status
    status_code = Column(Integer, nullable=True)  # HTTP status or operation status
    success = Column(Integer, default=1, nullable=False)  # 1=success, 0=failure

    # Error Information
    error_message = Column(Text, nullable=True)

    # Additional Context
    reason = Column(Text, nullable=True)  # Reason for the action
    admin_id = Column(Integer, nullable=True)  # Admin who triggered if not user
    extra_metadata = Column(JSON, nullable=True)

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action}, resource={self.resource_type})>"
