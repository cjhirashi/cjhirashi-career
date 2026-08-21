"""
Pydantic schemas - Agent Bedrock chat, model switching, and usage metrics.
"""
from datetime import date
from typing import List

from pydantic import BaseModel, ConfigDict

# Every schema below has a `model_id` field (an AWS Bedrock model id, not
# related to Pydantic's own `model_*` methods) - silence Pydantic v2's
# protected-namespace warning for that name across this whole module rather
# than renaming a field that matches the concept everywhere else (config.py,
# bedrock_service.py, the frontend).
_ALLOW_MODEL_ID = ConfigDict(protected_namespaces=())


class BedrockChatRequest(BaseModel):
    """The harness owns conversation history server-side, keyed by
    `session_id` (client-generated, >=33 chars - see bedrockChatStore.ts) -
    the client only ever sends the newest message, never the full history."""

    session_id: str
    message: str


class BedrockChatResponse(BaseModel):
    reply: str
    affected_resources: List[str] = []


class BedrockModelOption(BaseModel):
    model_config = _ALLOW_MODEL_ID

    model_id: str
    label: str
    price_input_per_million: float
    price_output_per_million: float


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
