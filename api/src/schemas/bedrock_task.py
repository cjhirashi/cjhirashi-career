"""
Pydantic schemas - Agent Bedrock's task/plan tracker (see models/bedrock_task.py).
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class BedrockTaskBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    status: str = Field(default="pending", max_length=20)


class BedrockTaskCreate(BedrockTaskBase):
    pass


class BedrockTaskUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = Field(None, max_length=20)


class BedrockTaskResponse(BedrockTaskBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
