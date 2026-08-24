"""
Loop agente local — Converse + tools + historial PG + delegación.

Punto de entrada del Harness local. Ver ADR-008.
"""
import json
import logging
from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from services.bedrock import agent_profiles, budget, converse_client, history_manager, prompt, section_profiles
from services.bedrock import settings_loader, tools, usage_logger
from services.bedrock.agent_profiles import resolve_agent_profile
from services.bedrock.delegation import run_specialist_sub_turn
from services.bedrock.attachments import build_user_content_blocks
from services.bedrock.errors import BedrockBudgetExceeded, BedrockError

logger = logging.getLogger(__name__)

_TOOL_STATUS = {
    "describe_resource_schema": "Revisando la estructura de la tabla...",
    "search_knowledge_base": "Consultando la base de conocimiento...",
    "list_career_record": "Buscando registros...",
    "get_career_record": "Consultando el registro...",
    "create_career_record": "Creando el registro...",
    "update_career_record": "Actualizando el registro...",
    "delete_career_record": "Eliminando el registro...",
    "list_recent_changes": "Consultando la bitácora...",
    "restore_deleted_record": "Restaurando el registro...",
    "create_linkedin_post": "Publicando en LinkedIn...",
    "generate_image": "Generando imagen...",
    "delegate_to_specialist": "Consultando especialista...",
    "list_job_providers": "Revisando portales de vacantes...",
    "run_job_discovery": "Buscando vacantes...",
    "import_job_url": "Importando vacante por URL...",
    "save_job_listings": "Creando vacantes autorizadas...",
}


@dataclass
class ChatTurnRequest:
    session_id: str
    message: str
    chat_surface: str = "contextual"
    page_context: Optional[Dict[str, Any]] = None
    model_id: Optional[str] = None
    agent_profile_id: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None


def _effective_model(req: ChatTurnRequest, runtime, profile) -> str:
    if req.model_id and req.model_id in settings.BEDROCK_AVAILABLE_MODELS:
        return req.model_id
    if req.chat_surface == "general":
        return runtime.orchestrator_model_id
    if profile.default_model_id:
        return profile.default_model_id
    return section_profiles.resolve_recommended_model(req.page_context)


async def run_single_turn_sync(
    db: AsyncSession,
    *,
    user_id: str,
    session_id: str,
    message: str,
    chat_surface: str = "contextual",
    agent_profile_id: Optional[str] = None,
    page_context: Optional[dict] = None,
    model_id: Optional[str] = None,
    max_round_trips: Optional[int] = None,
    record_history: bool = True,
) -> Dict[str, Any]:
    """Turno síncrono (sin SSE) — usado por delegación."""
    last: Dict[str, Any] = {}
    async for event in chat_stream(
        db,
        user_id,
        ChatTurnRequest(
            session_id=session_id,
            message=message,
            chat_surface=chat_surface,
            page_context=page_context,
            model_id=model_id,
            agent_profile_id=agent_profile_id,
        ),
        max_round_trips_override=max_round_trips,
        record_history=record_history,
    ):
        if event["type"] == "done":
            last = event
        elif event["type"] == "error":
            raise BedrockError(event["message"])
    return last


async def chat_stream(
    db: AsyncSession,
    user_id: str,
    req: ChatTurnRequest,
    *,
    max_round_trips_override: Optional[int] = None,
    record_history: bool = True,
) -> AsyncIterator[Dict[str, Any]]:
    """Generador SSE: status, delegation_*, done, error."""
    runtime = await settings_loader.get_runtime_settings(db)
    await budget.assert_budget_available(db, user_id, runtime.daily_budget_usd)

    profile = resolve_agent_profile(
        chat_surface=req.chat_surface,
        agent_profile_id=req.agent_profile_id,
        page_context=req.page_context,
    )
    model_id = _effective_model(req, runtime, profile)
    system_prompt = await prompt.compose_system_prompt(db, profile, req.page_context)

    allowed = agent_profiles.tools_for_profile(profile, tools.all_tool_names())
    tool_specs = tools.converse_tool_specs(allowed)

    session_type = "general" if req.chat_surface == "general" else "contextual"
    conversation = None
    history = await history_manager.load_converse_messages(db, user_id, req.session_id, runtime.history_window)
    user_content = await build_user_content_blocks(db, user_id, req.message, req.attachments)
    messages = history + [{"role": "user", "content": user_content}]

    if record_history:
        conversation = await history_manager.get_or_create_conversation(
            db, user_id, req.session_id, req.message, session_type=session_type
        )

    affected: List[str] = []
    total_usage = {"inputTokens": 0, "outputTokens": 0}
    max_rounds = max_round_trips_override or runtime.max_round_trips
    delegations_used = 0

    yield {"type": "status", "message": "Pensando..."}

    for _ in range(max_rounds):
        try:
            result = await converse_client.converse(
                model_id=model_id,
                messages=messages,
                system_prompt=system_prompt,
                tools=tool_specs,
            )
        except BedrockError as e:
            yield {"type": "error", "message": str(e)}
            return

        total_usage["inputTokens"] += result["usage"]["inputTokens"]
        total_usage["outputTokens"] += result["usage"]["outputTokens"]
        await usage_logger.record_round_log(
            user_id=user_id,
            session_id=req.session_id,
            model_id=model_id,
            round_type="converse",
            usage=result["usage"],
            agent_profile_id=profile.id,
        )

        if result["stop_reason"] != "tool_use":
            await usage_logger.record_turn_usage(user_id, req.session_id, model_id, total_usage)
            if record_history and conversation:
                await history_manager.append_message(db, conversation, "user", req.message)
                await history_manager.append_message(db, conversation, "assistant", result["text"])
            yield {"type": "done", "reply": result["text"], "affected_resources": affected}
            return

        for t in result["tool_uses"]:
            yield {"type": "status", "message": _TOOL_STATUS.get(t["name"], f"Usando {t['name']}...")}

        assistant_content = [
            {"toolUse": {"toolUseId": t["toolUseId"], "name": t["name"], "input": t["input"]}}
            for t in result["tool_uses"]
        ]
        tool_result_content = []

        for t in result["tool_uses"]:
            name = t["name"]
            try:
                if name == "delegate_to_specialist":
                    if req.chat_surface != "general":
                        tool_result = {"error": "delegation only in general chat"}
                    elif delegations_used >= settings.BEDROCK_MAX_DELEGATIONS_PER_TURN:
                        tool_result = {"error": "max delegations per turn exceeded"}
                    else:
                        spec_id = t["input"].get("agent_profile_id", "")
                        yield {
                            "type": "delegation_start",
                            "agent_profile_id": spec_id,
                            "label": agent_profiles.get_profile(spec_id).label,
                            "task_preview": (t["input"].get("task") or "")[:120],
                        }
                        sub = await run_specialist_sub_turn(
                            db,
                            user_id=user_id,
                            session_id=req.session_id,
                            profile=agent_profiles.get_profile(spec_id),
                            task=t["input"].get("task", ""),
                            context=t["input"].get("context"),
                        )
                        delegations_used += 1
                        tool_result = sub
                        yield {
                            "type": "delegation_end",
                            "agent_profile_id": spec_id,
                            "success": True,
                            "summary_preview": sub.get("summary", "")[:200],
                        }
                else:
                    tool_result = await tools.execute_tool(db, user_id, name, t["input"], req.session_id)
                status = "success"
                if name == "delegate_to_specialist" and isinstance(tool_result, dict):
                    for key in tool_result.get("affected_resources") or []:
                        if key not in affected:
                            affected.append(key)
                inv_key = tools.invalidation_key(name, t["input"], tool_result)
                if inv_key and inv_key not in affected:
                    affected.append(inv_key)
            except Exception as e:
                tool_result = {"error": str(e)}
                status = "error"

            tool_result_content.append({
                "toolResult": {
                    "toolUseId": t["toolUseId"],
                    "content": [{"text": json.dumps(tool_result, ensure_ascii=False, default=str)}],
                    "status": status,
                }
            })

        messages.extend([
            {"role": "assistant", "content": assistant_content},
            {"role": "user", "content": tool_result_content},
        ])

    await usage_logger.record_turn_usage(user_id, req.session_id, model_id, total_usage)
    yield {"type": "error", "message": "Se agotaron las vueltas del agente sin respuesta final."}


def use_local_harness() -> bool:
    """True si el Harness local está activo (default cuando flag=true)."""
    if not settings.BEDROCK_USE_LOCAL_HARNESS:
        return False
    if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
        return True
    return False
