"""
Pydantic schemas for FileUpload (MinIO bucket file management).
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class FileUploadResponse(BaseModel):
    id: int
    user_id: int
    original_filename: str
    stored_filename: str
    file_type: str
    mime_type: Optional[str] = None
    file_size: int
    description: Optional[str] = None
    is_public: bool
    download_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
