"""Esquema de la subtarea anidada (traslado de `SubtaskInput` de `cjhirashi-career-api/src/schemas/bedrock_task.py`).

Valida y rellena defaults igual que la API (D-13): campos omitidos vuelven a su default, `title` es
obligatorio y un `ValidationError` (no un `IntegrityError`) es lo que ve quien llama.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from models.bedrock_task import TASK_ASSIGNEE_TYPES, TASK_PRIORITIES, TASK_STATUSES
from services.agent_profiles import known_agent_profile_ids


class SubtaskInput(BaseModel):
    """Hija enviada anidada en create/update del padre. `parent_id` lo pone el servidor."""

    id: Optional[str] = Field(default=None, max_length=20)
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
        normalized = value.strip() if value is not None else None
        if not normalized:
            return None
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
