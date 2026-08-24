"""
Pydantic schemas for FileUpload (MinIO bucket file management).
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class FileUploadResponse(BaseModel):
    id: str
    user_id: str
    original_filename: str
    stored_filename: str
    file_type: str
    mime_type: Optional[str] = None
    file_size: int
    description: Optional[str] = None
    is_public: bool
    download_url: Optional[str] = None
    created_at: datetime
    notes: Optional[str] = None

    class Config:
        from_attributes = True
