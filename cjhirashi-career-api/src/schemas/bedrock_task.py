"""
Pydantic schemas — tablero de tareas (usuario o agente, padre o subtarea).
Ver models/bedrock_task.py y ADR-015 / ADR-016.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from models.agent_system_tasks import TASK_ASSIGNEE_TYPES, TASK_PRIORITIES, TASK_STATUSES


def _normalize_optional_str(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


class AgentSystemTaskBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    status: str = Field(default="pending", max_length=20)
    notes: Optional[str] = None
    assignee_type: str = Field(default="user", max_length=20)
    agent_profile_id: Optional[str] = Field(default=None, max_length=50)
    scheduled_at: Optional[datetime] = None
    due_at: Optional[datetime] = None
    priority: str = Field(default="medium", max_length=20)
    parent_id: Optional[str] = Field(default=None, max_length=20)
    sort_order: int = Field(default=0)
    is_blocking: bool = True
    execute_on_turn: bool = False


# Shared write-side validation (Create/Update/subtasks). Deliberately NOT on
# AgentSystemTaskBase: AgentSystemTaskResponse also extends it, and a row whose
# status/priority/agent_profile_id no longer matches current allowed values
# (e.g. a renamed or removed agent profile) must still be readable, or every
# GET on this resource 500s until someone edits that one record.
class _TaskWriteValidation:
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
            self.execute_on_turn = False
        if self.scheduled_at and self.due_at and self.due_at < self.scheduled_at:
            raise ValueError("due_at no puede ser anterior a scheduled_at")
        return self


class SubtaskInput(_TaskWriteValidation, AgentSystemTaskBase):
    """Hija enviada anidada en create/update del padre. `parent_id` lo pone el servidor."""

    id: Optional[str] = Field(default=None, max_length=20)
    parent_id: Optional[str] = Field(default=None, max_length=20)


class AgentSystemTaskCreate(_TaskWriteValidation, AgentSystemTaskBase):
    subtasks: Optional[List[SubtaskInput]] = None


class AgentSystemTaskUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = Field(None, max_length=20)
    notes: Optional[str] = None
    assignee_type: Optional[str] = Field(None, max_length=20)
    agent_profile_id: Optional[str] = Field(None, max_length=50)
    scheduled_at: Optional[datetime] = None
    due_at: Optional[datetime] = None
    priority: Optional[str] = Field(None, max_length=20)
    parent_id: Optional[str] = Field(None, max_length=20)
    sort_order: Optional[int] = None
    is_blocking: Optional[bool] = None
    execute_on_turn: Optional[bool] = None
    subtasks: Optional[List[SubtaskInput]] = None

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
            if self.execute_on_turn is True:
                self.execute_on_turn = False
        if self.scheduled_at and self.due_at and self.due_at < self.scheduled_at:
            raise ValueError("due_at no puede ser anterior a scheduled_at")
        return self


class AgentSystemTaskResponse(AgentSystemTaskBase):
    id: str
    user_id: str
    execution_result: Optional[str] = None
    executed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    turn_notified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
