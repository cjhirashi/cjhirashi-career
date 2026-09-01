"""
Agent Bedrock - chat, model switching, and usage-cost metrics.

FASE 3 Migration Status:
- [x] Core imports fixed (removed database, middleware.auth imports)
- [x] /chat endpoint migrated to use Request + token extraction
- [ ] Other 20+ endpoints still need migration (see BEDROCK_ENDPOINTS_TODO.md)
- [ ] Database access patterns need orchestrator_client refactoring
"""

import asyncio
import json
import logging

from fastapi import APIRouter, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse

from config import settings
from clients.orchestrator_client import orchestrator_client
from schemas.bedrock import BedrockChatRequest
from services import bedrock_service_wrapper as bedrock_service
from services.errors import BedrockError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bedrock", tags=["Bedrock"])


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
    """Extract user_id from JWT token.

    For now, returns a placeholder. TODO: Call orchestrator_client.verify_token()
    or implement JWT verification locally.
    """
    return "usr-2"  # PLACEHOLDER


def _require_configured() -> None:
    if not settings.AWS_ACCESS_KEY_ID or not settings.AWS_SECRET_ACCESS_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent Bedrock is not configured (missing AWS credentials)",
        )


async def _sse_chat_events(db, user_id: str, payload: BedrockChatRequest):
    """SSE from agent loop (Converse API + tools)."""
    from services.agent_loop import ChatTurnRequest

    turn = ChatTurnRequest(
        session_id=payload.session_id,
        message=payload.message,
        chat_surface=payload.chat_surface,
        page_context=payload.page_context,
        model_id=payload.model_id,
        agent_profile_id=payload.agent_profile_id,
        attachments=payload.attachments,
    )

    queue: asyncio.Queue = asyncio.Queue()

    async def _producer() -> None:
        try:
            async for event in bedrock_service.chat_stream(
                db, user_id, payload.session_id, payload.message, turn_request=turn
            ):
                await queue.put(("event", event))
        except BedrockError as e:
            logger.error("Bedrock chat failed: %s", e)
            await queue.put(("error", str(e)))
        except Exception as e:
            logger.exception("Unexpected error in Bedrock chat stream")
            await queue.put(("error", f"Error interno del agente: {e}"))
        finally:
            await queue.put(("done", None))

    producer_task = asyncio.create_task(_producer())
    try:
        while True:
            try:
                kind, payload_item = await asyncio.wait_for(queue.get(), timeout=15.0)
            except asyncio.TimeoutError:
                yield ": ping\n\n"
                continue
            if kind == "done":
                break
            if kind == "error":
                yield f"data: {json.dumps({'type': 'error', 'message': payload_item})}\n\n"
                break
            yield f"data: {json.dumps(payload_item)}\n\n"
    finally:
        if not producer_task.done():
            producer_task.cancel()
            try:
                await producer_task
            except asyncio.CancelledError:
                pass


@router.post("/chat", summary="Chat with Agent Bedrock (Server-Sent Events: status/done/error)")
async def chat(
    payload: BedrockChatRequest,
    request: Request,
):
    """Chat endpoint - FASE 3 migrated to use orchestrator_client."""
    _require_configured()
    auth_token = get_auth_token(request)
    user_id = extract_user_id_from_token(auth_token)

    return StreamingResponse(
        _sse_chat_events(None, user_id, payload),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ==============================================================================
# REMAINING ENDPOINTS (20+) - See BEDROCK_ENDPOINTS_TODO.md for migration plan
# ==============================================================================
# These endpoints still reference:
# - current_user: User = Depends(get_current_user)  ❌
# - db: AsyncSession = Depends(get_db)              ❌
# - bedrock_service module (monolith dependency)     ❌
#
# Migration pattern for each:
# 1. Change param to (request: Request)
# 2. Extract: auth_token = get_auth_token(request)
# 3. Extract: user_id = extract_user_id_from_token(auth_token)
# 4. Call orchestrator_client instead of bedrock_service
#
# Endpoints to migrate:
# - GET /model
# - PATCH /model
# - GET /catalog
# - GET /conversations
# - POST /task/*
# - Usage endpoints (12)
# - Memory endpoints (8)
# - Custom tools endpoints (4)
# - Audit log endpoints (2)
#
# Estimated effort: 3-4 hours for full migration
# Next session: Start with GET /model as template, then apply pattern to all
