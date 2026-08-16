"""
File Upload Model - File storage and management.
"""
from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, BigInteger, Boolean, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
import enum


class FileType(str, enum.Enum):
    """Type of uploaded file."""
    DOCUMENT = "document"  # PDF, DOC, DOCX
    IMAGE = "image"  # JPG, PNG, GIF
    ARCHIVE = "archive"  # ZIP, RAR, TAR
    OTHER = "other"


class FileUpload(Base):
    """
    User file upload storage and metadata.

    Supports:
    - File uploads for evidence and supporting documents
    - File metadata and versioning
    - Access control and permissions
    """

    __tablename__ = "file_uploads"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Foreign Key
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # File Metadata
    original_filename = Column(String(500), nullable=False)
    stored_filename = Column(String(500), unique=True, nullable=False, index=True)
    file_path = Column(String(1000), nullable=False)
    file_type = Column(Enum(FileType), nullable=False, index=True)
    mime_type = Column(String(100), nullable=True)
    file_size = Column(BigInteger, nullable=False)  # Size in bytes

    # File Details
    description = Column(String(500), nullable=True)
    category = Column(String(100), nullable=True, index=True)
    tags = Column(String(500), nullable=True)

    # Related Entity
    related_evidence_id = Column(Integer, nullable=True)  # FK to Evidence
    related_entity_type = Column(String(100), nullable=True)  # evidence, interview, project, etc.

    # Access Control
    is_public = Column(Boolean, default=False, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    download_count = Column(Integer, default=0, nullable=False)

    # URLs
    download_url = Column(String(500), nullable=True)
    preview_url = Column(String(500), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_downloaded = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="file_uploads")

    def __repr__(self):
        return f"<FileUpload(id={self.id}, filename='{self.original_filename}', size={self.file_size})>"
