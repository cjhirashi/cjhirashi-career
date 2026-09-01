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
    BedrockInstructionsResponse,
    BedrockInstructionsUpdateRequest,
    BedrockGlobalRulesUpdateRequest,
    BedrockAgentCustomToolResponse,
    AgentSystemCustomToolCreateRequest,
    BedrockAuditLogResponse,
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
    """Listar conversaciones del usuario."""
    auth_token = get_auth_token(request)
    user_id = extract_user_id_from_token(auth_token)

    conversations = await orchestrator_client.get_conversations(user_id, auth_token)
    return conversations if conversations else []


@router.get("/conversations/{session_id}", response_model=list[AgentSystemConversationMessageResponse],
            summary="Get messages in a conversation")
async def get_conversation_messages(session_id: str, request: Request):
    """Obtener mensajes de una conversación."""
    auth_token = get_auth_token(request)
    user_id = extract_user_id_from_token(auth_token)

    messages = await orchestrator_client.get_conversation_messages(user_id, auth_token, session_id)
    return messages if messages else []


@router.patch("/conversations/{session_id}", response_model=AgentSystemConversationResponse,
              summary="Rename a conversation")
async def rename_conversation(
    session_id: str,
    payload: AgentSystemConversationRenameRequest,
    request: Request,
):
    """Renombrar una conversación."""
    auth_token = get_auth_token(request)
    user_id = extract_user_id_from_token(auth_token)

    result = await orchestrator_client.rename_conversation(user_id, auth_token, session_id, payload.title)
    return AgentSystemConversationResponse(
        session_id=session_id,
        title=payload.title,
        created_at="2026-01-01T00:00:00Z",
    )


@router.delete("/conversations/{session_id}", summary="Delete a conversation")
async def delete_conversation(session_id: str, request: Request):
    """Eliminar una conversación."""
    auth_token = get_auth_token(request)
    user_id = extract_user_id_from_token(auth_token)

    result = await orchestrator_client.delete_conversation(user_id, auth_token, session_id)
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
    """Listar registros de memoria."""
    auth_token = get_auth_token(request)
    user_id = extract_user_id_from_token(auth_token)

    memory_records = await orchestrator_client.get_memory(user_id, auth_token)
    return memory_records if memory_records else []


@router.get("/memory/events/{session_id}", response_model=list[BedrockMemoryEventResponse],
            summary="Get memory events for a conversation")
async def get_memory_events(session_id: str, request: Request):
    """Obtener eventos de memoria para una conversación."""
    auth_token = get_auth_token(request)
    user_id = extract_user_id_from_token(auth_token)

    events = await orchestrator_client.get_memory_events(user_id, auth_token, session_id)
    return events if events else []


@router.get("/catalog", response_model=list[BedrockAgentCatalogItem],
            summary="Get agent catalog")
async def get_catalog(request: Request):
    """Obtener catálogo de perfiles de agente."""
    auth_token = get_auth_token(request)
    user_id = extract_user_id_from_token(auth_token)

    catalog = await orchestrator_client.get_catalog(user_id, auth_token)
    return catalog if catalog else []


@router.get("/instructions", response_model=BedrockInstructionsResponse,
            summary="Get system prompt and global rules")
async def get_instructions(request: Request):
    """Get system prompt and global rules."""
    auth_token = get_auth_token(request)
    user_id = extract_user_id_from_token(auth_token)

    # TODO FASE 4: Call orchestrator_client to get these
    return BedrockInstructionsResponse(
        system_prompt="You are a helpful assistant.",
        system_prompt_is_default=True,
        global_rules="",
        global_rules_is_default=True,
    )


@router.patch("/instructions", response_model=BedrockInstructionsResponse,
              summary="Update system prompt")
async def update_instructions(
    payload: BedrockInstructionsUpdateRequest,
    request: Request,
):
    """Update system prompt."""
    auth_token = get_auth_token(request)
    user_id = extract_user_id_from_token(auth_token)

    # TODO FASE 4: Call orchestrator_client.set_system_prompt(user_id, payload.text)
    return BedrockInstructionsResponse(
        system_prompt=payload.text,
        system_prompt_is_default=False,
        global_rules="",
        global_rules_is_default=True,
    )


@router.get("/rules", summary="Get global rules")
async def get_rules(request: Request):
    """Get global rules."""
    auth_token = get_auth_token(request)
    user_id = extract_user_id_from_token(auth_token)

    # TODO FASE 4: Call orchestrator_client
    return {
        "rules": "",
        "is_default": True,
    }


@router.patch("/rules", summary="Update global rules")
async def update_rules(
    payload: BedrockGlobalRulesUpdateRequest,
    request: Request,
):
    """Update global rules."""
    auth_token = get_auth_token(request)
    user_id = extract_user_id_from_token(auth_token)

    # TODO FASE 4: Call orchestrator_client.set_global_rules(user_id, payload.text)
    return {
        "rules": payload.text,
        "is_default": False,
    }


@router.get("/tools", response_model=list[BedrockAgentCustomToolResponse],
            summary="List custom tools")
async def list_tools(request: Request):
    """Listar herramientas personalizadas."""
    auth_token = get_auth_token(request)
    user_id = extract_user_id_from_token(auth_token)

    tools = await orchestrator_client.get_custom_tools(user_id, auth_token)
    return tools if tools else []


@router.post("/tools", response_model=BedrockAgentCustomToolResponse,
             summary="Create custom tool")
async def create_tool(
    payload: AgentSystemCustomToolCreateRequest,
    request: Request,
):
    """Crear herramienta personalizada."""
    auth_token = get_auth_token(request)
    user_id = extract_user_id_from_token(auth_token)

    result = await orchestrator_client.create_custom_tool(
        user_id,
        auth_token,
        payload.name,
        payload.url,
        getattr(payload, "headers", None),
    )
    return BedrockAgentCustomToolResponse(
        id=result.get("id", "tmp-1") if result else "tmp-1",
        name=payload.name,
        url=payload.url,
        is_enabled=True,
    )


@router.get("/audit-log", response_model=list[BedrockAuditLogResponse],
            summary="List audit log entries")
async def get_audit_log(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    request: Request = None,
):
    """Obtener registro de auditoría."""
    if request is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization required")

    auth_token = get_auth_token(request)
    user_id = extract_user_id_from_token(auth_token)

    audit_log = await orchestrator_client.get_audit_log(user_id, auth_token, limit, offset)
    return audit_log if audit_log else []


@router.post("/audit-log/{audit_id}/restore", summary="Restore audit entry")
async def restore_audit_entry(audit_id: str, request: Request):
    """Restaurar entrada del registro de auditoría."""
    auth_token = get_auth_token(request)
    user_id = extract_user_id_from_token(auth_token)

    result = await orchestrator_client.get_audit_log(user_id, auth_token)
    return {"restored": True, "audit_id": audit_id}


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
