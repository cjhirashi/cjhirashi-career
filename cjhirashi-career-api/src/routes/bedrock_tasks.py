"""
Tablero de tareas — CRUD genérico bajo `/agent-tasks` (el prefijo se conserva por compatibilidad con el Admin).
"""
from models.bedrock_task import BedrockTask
from routes.career_common import build_crud_router
from schemas.bedrock_task import BedrockTaskCreate, BedrockTaskResponse, BedrockTaskUpdate

router = build_crud_router(
    prefix="/agent-tasks",
    tags=["Agent - Tasks"],
    model=BedrockTask,
    create_schema=BedrockTaskCreate,
    update_schema=BedrockTaskUpdate,
    response_schema=BedrockTaskResponse,
    entity_name="tarea",
)
