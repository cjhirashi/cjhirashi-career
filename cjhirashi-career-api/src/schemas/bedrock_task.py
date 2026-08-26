"""
Pydantic schemas — tablero de tareas (usuario o agente). Ver models/bedrock_task.py y ADR-015.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from models.bedrock_task import TASK_ASSIGNEE_TYPES, TASK_PRIORITIES, TASK_STATUSES


def _normalize_optional_str(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


class BedrockTaskBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    status: str = Field(default="pending", max_length=20)
    notes: Optional[str] = None
    assignee_type: str = Field(default="user", max_length=20)
    agent_profile_id: Optional[str] = Field(default=None, max_length=50)
    scheduled_at: Optional[datetime] = None
    due_at: Optional[datetime] = None
    priority: str = Field(default="medium", max_length=20)

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in TASK_STATUSES:
            raise ValueError(f"status debe ser uno de: {', '.join(TASK_STATUSES)}")
        return value

    @field_validator("assignee_type")
    @classmethod
    def validate_assignee_type(cls, value: str) -> str:
        if value not in TASK_ASSIGNEE_TYPES:
            raise ValueError(f"assignee_type debe ser uno de: {', '.join(TASK_ASSIGNEE_TYPES)}")
        return value

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, value: str) -> str:
        if value not in TASK_PRIORITIES:
            raise ValueError(f"priority debe ser uno de: {', '.join(TASK_PRIORITIES)}")
        return value

    @field_validator("agent_profile_id")
    @classmethod
    def validate_agent_profile_id(cls, value: Optional[str]) -> Optional[str]:
        normalized = _normalize_optional_str(value)
        if normalized is None:
            return None
        from services.bedrock.agent_profiles import known_agent_profile_ids

        if normalized not in known_agent_profile_ids():
            raise ValueError(f"Agente desconocido: {normalized}")
        return normalized

    @model_validator(mode="after")
    def assignee_consistency(self):
        if self.assignee_type == "agent" and not self.agent_profile_id:
            raise ValueError("agent_profile_id es obligatorio cuando assignee_type=agent")
        if self.assignee_type == "user":
            self.agent_profile_id = None
        if self.scheduled_at and self.due_at and self.due_at < self.scheduled_at:
            raise ValueError("due_at no puede ser anterior a scheduled_at")
        return self


class BedrockTaskCreate(BedrockTaskBase):
    pass


class BedrockTaskUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = Field(None, max_length=20)
    notes: Optional[str] = None
    assignee_type: Optional[str] = Field(None, max_length=20)
    agent_profile_id: Optional[str] = Field(None, max_length=50)
    scheduled_at: Optional[datetime] = None
    due_at: Optional[datetime] = None
    priority: Optional[str] = Field(None, max_length=20)

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        if value not in TASK_STATUSES:
            raise ValueError(f"status debe ser uno de: {', '.join(TASK_STATUSES)}")
        return value

    @field_validator("assignee_type")
    @classmethod
    def validate_assignee_type(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        if value not in TASK_ASSIGNEE_TYPES:
            raise ValueError(f"assignee_type debe ser uno de: {', '.join(TASK_ASSIGNEE_TYPES)}")
        return value

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        if value not in TASK_PRIORITIES:
            raise ValueError(f"priority debe ser uno de: {', '.join(TASK_PRIORITIES)}")
        return value

    @field_validator("agent_profile_id")
    @classmethod
    def validate_agent_profile_id(cls, value: Optional[str]) -> Optional[str]:
        normalized = _normalize_optional_str(value)
        if normalized is None:
            return None
        from services.bedrock.agent_profiles import known_agent_profile_ids

        if normalized not in known_agent_profile_ids():
            raise ValueError(f"Agente desconocido: {normalized}")
        return normalized

    @model_validator(mode="after")
    def assignee_consistency(self):
        if self.assignee_type == "agent" and self.agent_profile_id is None:
            raise ValueError("agent_profile_id es obligatorio cuando assignee_type=agent")
        if self.assignee_type == "user":
            self.agent_profile_id = None
        if self.scheduled_at and self.due_at and self.due_at < self.scheduled_at:
            raise ValueError("due_at no puede ser anterior a scheduled_at")
        return self


class BedrockTaskResponse(BedrockTaskBase):
    id: str
    user_id: str
    execution_result: Optional[str] = None
    executed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
