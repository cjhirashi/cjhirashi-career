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

# ============================================================================
# Constantes de estado de tools
# ============================================================================

_TOOL_STATUS = {
    "describe_resource_schema": "Revisando la estructura de la tabla...",
    "search_knowledge_base": "Consultando la base de conocimiento...",
    "list_career_record": "Buscando registros...",
    "count_career_records": "Contando registros...",
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


# ============================================================================
# Dataclass que modela la solicitud de un turno de chat realizado por el usuario.
# Contiene el mensaje principal, contexto del chat, información de metadatos de página,
# perfil/agente relevante, modelo de IA preferido y anexos enviados junto al mensaje.
# Es usada como estructura base para manejar la información de cada petición de conversación.
# ============================================================================

@dataclass
class ChatTurnRequest:
    session_id: str                # ID único de la sesión de chat
    message: str                   # Mensaje enviado por el usuario (input principal)
    chat_surface: str = "contextual"         # Superficie/contexto del chat ("general", "contextual", etc.)
    page_context: Optional[Dict[str, Any]] = None  # Contexto adicional de la página/origen (metadatos relevantes)
    model_id: Optional[str] = None           # ID explícito del modelo solicitado (opcional, sugerido por cliente)
    agent_profile_id: Optional[str] = None   # Perfil/agente especializado solicitado (opcional)
    attachments: Optional[List[Dict[str, Any]]] = None  # Archivos adjuntos o bloques de contenido enviados junto al mensaje


# ============================================================================
# Resolución de modelo efectivo
# ============================================================================

def _effective_model(req: ChatTurnRequest, runtime, profile) -> str:
    """
    Determina el modelo de IA "efectivo" para una solicitud de turno de chat,
    teniendo en cuenta las preferencias del usuario, reglas de negocio y perfiles de agente.

    - Para chats "general", ignora modelos débiles sugeridos por el usuario y usa el default del perfil
      si existe y está permitido, o el modelo por defecto del runtime.
    - Para otras superficies/contextos:
      - Si el usuario sugirió un modelo permitido y no es "débil", se usa ese.
      - Si no, prefiere el modelo por defecto del perfil, si existe.
      - Si ningún criterio anterior aplica, recomienda modelo según el contexto de página.

    Args:
        req:   Instancia de ChatTurnRequest con la metadata del turno.
        runtime: Objeto con configuración actual de orquestador de modelos.
        profile: Perfil de agente asociado a la conversación.

    Returns:
        str: ID del modelo efectivo a utilizar.
    """
    # Modelos considerados demasiado "débiles" para chats generales.
    weak_models = {
        "amazon.nova-lite-v1:0",
        "amazon.nova-micro-v1:0",
    }

    # Si la superficie es "general", se prefiere explícitamente el modelo por defecto del perfil,
    # ignorando modelos débiles sugeridos por el cliente.
    if req.chat_surface == "general":
        # Usa el modelo por defecto del perfil si está definido y está permitido.
        if profile.default_model_id and profile.default_model_id in settings.BEDROCK_AVAILABLE_MODELS:
            return profile.default_model_id
        # Si no existe, cae al modelo por defecto definido a nivel de runtime.
        return runtime.orchestrator_model_id

    # En otros chats/contextos, si el usuario pide un modelo explícito permitido (y no débil), usarlo.
    if req.model_id and req.model_id in settings.BEDROCK_AVAILABLE_MODELS:
        if req.model_id not in weak_models:
            return req.model_id

    # Si el perfil tiene un modelo por defecto valido, usarlo.
    if profile.default_model_id:
        return profile.default_model_id

    # Como última opción, recomendar modelo basado en el contexto de página actual.
    return section_profiles.resolve_recommended_model(req.page_context)


# ============================================================================
# Turno síncrono
# ============================================================================

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
    """
    Ejecuta un único turno de conversación de manera síncrona (sin streaming SSE) utilizando el loop principal del agente Bedrock.

    Este método es utilizado típicamente para delegación interna o desde componentes que requieren la respuesta
    completa del agente en una sola llamada, sin la comunicación parcial por eventos SSE.

    Flujo interno:
        - Invoca el generador `chat_stream`, iterando sobre los eventos generados por el agente.
        - Si se recibe un evento de tipo "done", lo almacena como resultado final.
        - Si se recibe un evento de tipo "error", se lanza la excepción correspondiente.
        - Al finalizar, devuelve el resultado completo de la respuesta (evento "done").

    Args:
        db (AsyncSession): Sesión async de base de datos.
        user_id (str): ID del usuario que realiza la solicitud.
        session_id (str): ID de la conversación/sesión.
        message (str): Mensaje o input del usuario.
        chat_surface (str, opcional): Superficie del chat ("general", "contextual", etc.).
        agent_profile_id (str, opcional): ID del perfil de agente.
        page_context (dict, opcional): Contexto de página o metadata adicional.
        model_id (str, opcional): Modelo explícito a usar en la respuesta.
        max_round_trips (int, opcional): Rondas máximas permitidas para el ciclo de herramientas.
        record_history (bool, opcional): Si True, registra el turno en el historial.

    Returns:
        Dict[str, Any]: Diccionario con la respuesta final generada (evento "done").
    
    Raises:
        BedrockError: Si se produce un error durante la generación del turno.
    """
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


# ============================================================================
# Turno con streaming SSE
# ============================================================================

async def chat_stream(
    db: AsyncSession,
    user_id: str,
    req: ChatTurnRequest,
    *,
    max_round_trips_override: Optional[int] = None,
    record_history: bool = True,
) -> AsyncIterator[Dict[str, Any]]:
    """
    Generador asincrónico de eventos para manejar el ciclo de conversación del agente con soporte para SSE (Server-Sent Events).
    
    Esta función permite procesar turnos de conversación entre un usuario y un agente, soportando múltiples rondas, 
    llamadas a herramientas y delegaciones a especialistas, todo en modalidad de streaming asíncrono. Produce distintos 
    eventos a lo largo del proceso, notificando sobre el estado, delegaciones, errores y la respuesta final.

    Flujo principal:
        1. Prepara el contexto de ejecución: recupera historial, perfil de agente, herramientas permitidas y mensaje actual.
        2. (Opcional) Registra o recupera la conversación en la BD, si record_history=True.
        3. Itera hasta un máximo de rondas (max_rounds): 
            - Llama al modelo conversacional para obtener la siguiente acción (respuesta o uso de herramienta).
            - Si hay error con Bedrock, emite un evento de error y termina.
            - Si el agente responde directamente (stop_reason != tool_use):
                - Registra uso y mensajes en historial, si corresponde.
                - Emite evento "done" con la respuesta final y termina.
            - Si requiere herramientas:
                - Para cada uso de herramienta:
                    - Si es delegación a especialista, ejecuta sub-turno y emite eventos de inicio/fin.
                    - Si es herramienta normal, la ejecuta y agrega resultados.
                    - Acumula recursos afectados e invalidaciones.
                - Agrega los resultados de herramientas al nuevo contexto para la siguiente ronda.
        4. Si se agotan las vueltas sin respuesta final, emite un evento de error.

    Args:
        db (AsyncSession): Sesión asíncrona de base de datos.
        user_id (str): ID del usuario que interactúa con el agente.
        req (ChatTurnRequest): Objeto con detalles del turno/mensaje y contexto.
        max_round_trips_override (int, opcional): Número máximo de rondas para la conversación (override de setting).
        record_history (bool, opcional): Si True, registra el historial de mensajes/conversación.

    Yields:
        Dict[str, Any]: Diccionario con eventos de tipo:
            - {"type": "status", "message": ...}
            - {"type": "delegation_start", ...}
            - {"type": "delegation_end", ...}
            - {"type": "done", "reply": ..., "affected_resources": [...]}
            - {"type": "error", "message": ...}

    Raises:
        BedrockError: Si ocurre un error durante la ejecución de la ronda conversacional (emite evento de error).
    """
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

    first_round = True
    for _ in range(max_rounds):
        try:
            result = await converse_client.converse(
                model_id=model_id,
                messages=messages,
                system_prompt=system_prompt,
                tools=tool_specs,
                force_tool_use=first_round and bool(tool_specs),
            )
        except BedrockError as e:
            yield {"type": "error", "message": str(e)}
            return
        first_round = False

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
