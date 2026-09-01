"""
Agent Tasks board - CRUD + autonomous execution.

FASE 3 Migration Status:
- [x] Imports fixed (removed database, middleware.auth)
- [x] run_task_now endpoint migrated to Request-based auth
- [ ] Full CRUD endpoints still need implementation
"""

import asyncio
import logging

from fastapi import APIRouter, HTTPException, Request, status

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent-tasks", tags=["Agent - Tasks"])


def get_auth_token(request: Request) -> str:
    """Extract Bearer token from Authorization header."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header"
        )
    return auth[7:]


def extract_user_id_from_token(auth_token: str) -> str:
    """Extract user_id from JWT token."""
    return "usr-2"  # PLACEHOLDER


@router.post(
    "/{item_id}/run",
    summary="Execute an agent task now",
)
async def run_task_now(
    item_id: str,
    request: Request,
):
    """Claim task and launch harness in background.

    Executes the same runner as the scheduler (ADR-015):
    the agent works without session SPA.
    """
    auth_token = get_auth_token(request)
    user_id = extract_user_id_from_token(auth_token)

    # TODO FASE 4:
    # task = await orchestrator_client.claim_task_for_user(user_id, item_id)
    # if task is None:
    #     raise HTTPException(
    #         status_code=status.HTTP_409_CONFLICT,
    #         detail="Task cannot be executed: must be assigned to an agent, pending/failed, with valid profile"
    #     )
    # asyncio.create_task(orchestrator_client.execute_task(task.id))

    return {
        "id": item_id,
        "status": "queued",
        "message": "Task execution queued (FASE 4: orchestrator_client integration pending)"
    }
