"""
Agent Tasks board - CRUD + autonomous execution.

FASE 3 Migration Status:
- [ ] Update run_task_now endpoint to use Request + token extraction
- [ ] Replace task_scheduler with orchestrator_client calls
- [ ] Migrate task CRUD to use orchestrator_client

Status: Pending - see BEDROCK_TASKS_TODO.md
"""

import logging
from fastapi import APIRouter, HTTPException, Request, status

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent-tasks", tags=["Agent - Tasks"])


# ============================================================================
# Original endpoint - needs migration in FASE 3 continuation
# ============================================================================
# @router.post(
#     "/{item_id}/run",
#     response_model=AgentSystemTaskResponse,
#     summary="Execute an agent task now",
# )
# async def run_task_now(
#     item_id: str,
#     request: Request,
# ):
#     """Claim task and launch harness in background."""
#     # TODO FASE 3:
#     # auth_token = get_auth_token(request)
#     # user_id = extract_user_id_from_token(auth_token)
#     # task = await orchestrator_client.claim_task_for_user(user_id, item_id)
#     # if task is None:
#     #     raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="...")
#     # await orchestrator_client.execute_task(task.id)
#     # return task
#     pass
