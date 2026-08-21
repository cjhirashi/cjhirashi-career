"""
Agent Bedrock's task/plan tracker - generic CRUD router, same
build_crud_router/CareerRepository machinery every career-domain resource
uses (see routes/career_common.py). Importing this module is what registers
"agent-tasks" into RESOURCE_REGISTRY, which is what makes it reachable by
the agent's existing generic tools (create_career_record etc.) with zero
new tool code - see services/bedrock_service.py.
"""
from models.bedrock_task import BedrockTask
from schemas.bedrock_task import BedrockTaskCreate, BedrockTaskUpdate, BedrockTaskResponse
from routes.career_common import build_crud_router

router = build_crud_router(
    prefix="/agent-tasks",
    tags=["Agent - Tasks"],
    model=BedrockTask,
    create_schema=BedrockTaskCreate,
    update_schema=BedrockTaskUpdate,
    response_schema=BedrockTaskResponse,
    entity_name="tarea del agente",
)
