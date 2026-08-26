from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UserNotificationResponse(BaseModel):
    id: str
    user_id: str
    kind: str
    title: str
    body: Optional[str] = None
    resource_key: Optional[str] = None
    resource_id: Optional[str] = None
    read_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UnreadCountResponse(BaseModel):
    count: int = Field(ge=0)
