"""
Pydantic schemas - Agent Bedrock chat, model switching, usage metrics,
instructions, custom tools, and memory.
"""
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict

# Every schema below has a `model_id` field (an AWS Bedrock model id, not
# related to Pydantic's own `model_*` methods) - silence Pydantic v2's
# protected-namespace warning for that name across this whole module rather
# than renaming a field that matches the concept everywhere else (config.py,
# bedrock_service.py, the frontend).
_ALLOW_MODEL_ID = ConfigDict(protected_namespaces=())


class BedrockChatRequest(BaseModel):
    """Harness local: historial en PG; cliente envía mensaje + contexto opcional."""

    session_id: str
    message: str
    chat_surface: str = "contextual"
    page_context: Optional[Dict[str, Any]] = None
    model_id: Optional[str] = None
    agent_profile_id: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None


class BedrockModelOption(BaseModel):
    model_config = _ALLOW_MODEL_ID

    model_id: str
    label: str
    price_input_per_million: float
    price_output_per_million: float
    tier: Optional[str] = None


class BedrockModelStatusResponse(BaseModel):
    current_model_id: str
    available_models: List[BedrockModelOption]


class BedrockModelSwitchRequest(BaseModel):
    model_config = _ALLOW_MODEL_ID

    model_id: str


class BedrockUsageByModel(BaseModel):
    model_config = _ALLOW_MODEL_ID

    model_id: str
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float
    turns: int


class BedrockUsageByDay(BaseModel):
    day: date
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float


class BedrockUsageMetricsResponse(BaseModel):
    by_model: List[BedrockUsageByModel]
    by_day: List[BedrockUsageByDay]
    total_estimated_cost_usd: float
    daily_budget_usd: Optional[float] = None
    daily_spent_usd: Optional[float] = None
    daily_remaining_usd: Optional[float] = None


class BedrockBudgetStatusResponse(BaseModel):
    daily_budget_usd: float
    daily_spent_usd: float
    daily_remaining_usd: float


class BedrockInstructionsResponse(BaseModel):
    system_prompt: str
    is_default: bool


class BedrockInstructionsUpdateRequest(BaseModel):
    """`system_prompt=None` (or omitted) resets to the built-in default."""

    system_prompt: Optional[str] = None


class BedrockCustomToolCreateRequest(BaseModel):
    name: str
    url: str
    headers: Optional[Dict[str, str]] = None


class BedrockCustomToolResponse(BaseModel):
    id: int
    name: str
    url: str
    headers: Optional[Dict[str, str]] = None
    is_enabled: bool
    created_at: datetime

    class Config:
        from_attributes = True


class BedrockMemoryRecordResponse(BaseModel):
    """Loosely typed on purpose - passes through whatever AgentCore Memory's
    API returns (memoryRecordId, content, score, createdAt, ...) rather than
    re-modeling its full response shape for a read-only diagnostic view."""

    memoryRecordId: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    score: Optional[float] = None
    createdAt: Optional[Any] = None
    namespaces: Optional[List[str]] = None

    class Config:
        extra = "allow"


class BedrockMemoryEventResponse(BaseModel):
    """Same rationale as BedrockMemoryRecordResponse - passes through the
    real Event shape (eventId, eventTimestamp, payload, ...)."""

    eventId: Optional[str] = None
    eventTimestamp: Optional[Any] = None
    payload: Optional[List[Dict[str, Any]]] = None

    class Config:
        extra = "allow"


class BedrockManualMemoryRequest(BaseModel):
    text: str


class BedrockConversationResponse(BaseModel):
    session_id: str
    title: str
    session_type: str = "contextual"
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BedrockConversationMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class BedrockConversationRenameRequest(BaseModel):
    title: str


class BedrockAuditLogResponse(BaseModel):
    id: int
    action: str
    resource_type: str
    resource_id: Optional[int] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True
