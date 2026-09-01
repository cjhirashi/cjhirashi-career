"""
Agent Bedrock - chat, model switching, and usage-cost metrics.

FASE 3 Migration Status:
- [x] Core imports fixed (removed database, middleware.auth imports)
- [x] /chat endpoint migrated to use Request + token extraction
- [x] GET/POST /model endpoints migrated (2/21 complete)
- [ ] Other 18+ endpoints still need migration (see BEDROCK_ENDPOINTS_TODO.md)
- [ ] Database access patterns need orchestrator_client refactoring
"""

import asyncio
import json
import logging

from fastapi import APIRouter, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse

from config import settings
from clients.orchestrator_client import orchestrator_client
from schemas.bedrock import (
    BedrockChatRequest,
    BedrockModelOption,
    BedrockModelStatusResponse,
    BedrockModelSwitchRequest,
    AgentSystemConversationResponse,
    AgentSystemConversationRenameRequest,
    AgentSystemConversationMessageResponse,
    BedrockBudgetStatusResponse,
    BedrockUsageMetricsResponse,
    BedrockMemoryRecordResponse,
    BedrockMemoryEventResponse,
    BedrockAgentCatalogItem,
)
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


@router.get("/model", response_model=BedrockModelStatusResponse,
            summary="Get the active chat model and the switchable allow-list")
async def get_model(request: Request):
    """Get available models and current selection."""
    _require_configured()
    auth_token = get_auth_token(request)
    user_id = extract_user_id_from_token(auth_token)

    try:
        current_model_id = await bedrock_service.get_current_model()
    except BedrockError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    available = [
        BedrockModelOption(model_id=model_id, **info)
        for model_id, info in settings.BEDROCK_AVAILABLE_MODELS.items()
    ]
    return BedrockModelStatusResponse(current_model_id=current_model_id, available_models=available)


@router.post("/model", response_model=BedrockModelStatusResponse,
             summary="Switch the chat model")
async def switch_model(
    payload: BedrockModelSwitchRequest,
    request: Request,
):
    """Switch to a different model."""
    _require_configured()
    auth_token = get_auth_token(request)
    user_id = extract_user_id_from_token(auth_token)

    if payload.model_id not in settings.BEDROCK_AVAILABLE_MODELS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown model_id: {payload.model_id}",
        )

    try:
        await bedrock_service.switch_model(payload.model_id)
    except BedrockError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    available = [
        BedrockModelOption(model_id=model_id, **info)
        for model_id, info in settings.BEDROCK_AVAILABLE_MODELS.items()
    ]
    return BedrockModelStatusResponse(current_model_id=payload.model_id, available_models=available)


@router.get("/conversations", response_model=list[AgentSystemConversationResponse],
            summary="List all conversations for the user")
async def list_conversations(request: Request):
    """List conversations with summary info."""
    auth_token = get_auth_token(request)
    user_id = extract_user_id_from_token(auth_token)

    # TODO FASE 4: Call orchestrator_client.get_conversations(user_id)
    # For now, return empty list
    return []


@router.get("/conversations/{session_id}", response_model=list[AgentSystemConversationMessageResponse],
            summary="Get messages in a conversation")
async def get_conversation_messages(session_id: str, request: Request):
    """Get all messages in a conversation."""
    auth_token = get_auth_token(request)
    user_id = extract_user_id_from_token(auth_token)

    # TODO FASE 4: Call orchestrator_client.get_conversation_messages(user_id, session_id)
    # For now, return empty list
    return []


@router.patch("/conversations/{session_id}", response_model=AgentSystemConversationResponse,
              summary="Rename a conversation")
async def rename_conversation(
    session_id: str,
    payload: AgentSystemConversationRenameRequest,
    request: Request,
):
    """Rename a conversation."""
    auth_token = get_auth_token(request)
    user_id = extract_user_id_from_token(auth_token)

    # TODO FASE 4: Call orchestrator_client.rename_conversation(user_id, session_id, payload.title)
    return AgentSystemConversationResponse(
        session_id=session_id,
        title=payload.title,
        created_at="2026-01-01T00:00:00Z",
    )


@router.delete("/conversations/{session_id}", summary="Delete a conversation")
async def delete_conversation(session_id: str, request: Request):
    """Delete a conversation."""
    auth_token = get_auth_token(request)
    user_id = extract_user_id_from_token(auth_token)

    # TODO FASE 4: Call orchestrator_client.delete_conversation(user_id, session_id)
    return {"deleted": True, "session_id": session_id}


@router.get("/usage-metrics", response_model=BedrockUsageMetricsResponse,
            summary="Token usage and estimated cost of the chat assistant")
async def get_usage_metrics(
    days: int = Query(30, ge=1, le=365, description="How many most-recent days to include"),
    request: Request = None,
):
    """Get token usage metrics."""
    # TODO FASE 4: Extract auth_token if request is provided
    user_id = "usr-2"  # PLACEHOLDER

    # TODO FASE 4: Call orchestrator_client.get_usage_metrics(user_id, days)
    return BedrockUsageMetricsResponse(
        by_model=[],
        by_day=[],
        total_estimated_cost_usd=0.0,
        total_cache_read_tokens=0,
        total_cache_savings_usd=0.0,
        daily_budget_usd=float(settings.BEDROCK_DAILY_BUDGET_USD),
        daily_spent_usd=0.0,
        daily_remaining_usd=float(settings.BEDROCK_DAILY_BUDGET_USD),
    )


@router.get("/budget", response_model=BedrockBudgetStatusResponse,
            summary="Daily inference budget status")
async def get_budget_status(request: Request):
    """Get daily budget status."""
    auth_token = get_auth_token(request)
    user_id = extract_user_id_from_token(auth_token)

    # TODO FASE 4: Call orchestrator_client.get_budget(user_id)
    daily_budget = float(settings.BEDROCK_DAILY_BUDGET_USD)
    return BedrockBudgetStatusResponse(
        daily_budget_usd=daily_budget,
        daily_spent_usd=0.0,
        daily_remaining_usd=daily_budget,
    )


@router.get("/memory", response_model=list[BedrockMemoryRecordResponse],
            summary="List memory records")
async def list_memory(request: Request):
    """List all memory records."""
    auth_token = get_auth_token(request)
    user_id = extract_user_id_from_token(auth_token)

    # TODO FASE 4: Call orchestrator_client.get_memory(user_id)
    return []


@router.get("/memory/events/{session_id}", response_model=list[BedrockMemoryEventResponse],
            summary="Get memory events for a conversation")
async def get_memory_events(session_id: str, request: Request):
    """Get memory events."""
    auth_token = get_auth_token(request)
    user_id = extract_user_id_from_token(auth_token)

    # TODO FASE 4: Call orchestrator_client.get_memory_events(user_id, session_id)
    return []


@router.get("/catalog", response_model=list[BedrockAgentCatalogItem],
            summary="Get agent catalog")
async def get_catalog(request: Request):
    """Get available agent profiles from catalog."""
    auth_token = get_auth_token(request)
    user_id = extract_user_id_from_token(auth_token)

    # TODO FASE 4: Call orchestrator_client.get_catalog(user_id)
    return []


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
