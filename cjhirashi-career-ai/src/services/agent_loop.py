"""Bucle de agente del harness (RF-005, T-085): Converse + tools + historial + delegación.

Traslado de `cjhirashi-career-api/src/services/bedrock/agent_loop.py` con tres adaptaciones:
el modelo se invoca por el `ModelProvider` inyectado (`provider.converse()`), las tools se ejecutan
con el `tool_executor` inyectado en el contexto del llamador (la credencial viaja por `contextvars`,
RF-004) y el perfil del turno se resuelve con el cliente REST de secciones (D-10).
Los colaboradores se acceden por atributo de módulo para poder sustituirlos en los tests.
"""
import json
import logging
import re
from dataclasses import dataclass
from typing import Any, AsyncIterator, Awaitable, Callable, Dict, List, Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from clients.api_client import ApiError
from clients.sections import SectionsClient
from config import settings
from providers.base import ModelProvider, ModelRequest, ProviderError, ToolSpec, Usage
from repositories import conversation_repo, profile_repo
from services import (
    agent_profiles,
    memory_service,
    profile_catalog,
    prompt,
    settings_loader,
    tools_registry,
    usage_service,
)
from services.attachments import build_user_content_blocks
from services.section_profiles import resolve_recommended_model

logger = logging.getLogger(__name__)

ToolExecutor = Callable[..., Awaitable[Any]]

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
    "bulk_update_career_record": "Actualizando varios registros...",
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
    "pdf_style": "Actualizando el estilo PDF...",
    "pdf_template": "Actualizando la plantilla PDF...",
    "generate_pdf": "Generando PDF...",
    "render_record_pdf": "Generando PDF del registro...",
    "list_pdf_capable_resources": "Revisando tablas con PDF...",
    "web_search": "Buscando en internet...",
    "web_fetch": "Leyendo la página...",
    "get_github_status": "Revisando la conexión GitHub...",
    "list_github_repos": "Listando repositorios GitHub...",
    "get_github_repo": "Consultando el repositorio...",
    "list_github_contents": "Listando archivos del repositorio...",
    "get_github_file": "Leyendo el archivo en GitHub...",
    "search_github_code": "Buscando código en GitHub...",
}

# Tools de solo lectura cuyo resultado no cambia dentro de un mismo turno: si el
# modelo repite la llamada idéntica, se le responde con una nota corta en vez de
# reejecutar y reincrustar el payload (control de tokens de entrada).
_DEDUP_READ_TOOLS = frozenset({
    "get_career_record",
    "list_career_record",
    "count_career_records",
    "describe_resource_schema",
    "search_knowledge_base",
})


# Si un L2 anuncia un write o el usuario pide guardar y el turno termina sin
# tool de escritura, un recordatorio (una vez) obliga a persistir.
# Ver should_nudge_persist. "ok" solo cuenta si el asistente reivindicó el write.
_USER_WRITE_INTENT = re.compile(
    r"(?i)\b(generar|generes|genera|guardar|guardes|guarda|actualizar|actualices|"
    r"actualiza|escribir|escribas|escribe|documentar|documenta|crear|crea|crees)\b"
)
_USER_PROCEED = re.compile(
    r"(?i)\b(procede|adelante|hazlo|apl[ií]calo|implementa(lo)?|contin[uú]a)\b"
)
_ASSISTANT_WRITE_CLAIM = re.compile(
    r"(?i)("
    r"ahora (actualizo|guardo|escribo|creo|reclasifico|clasifico|modifico|"
    r"cambio|reorganizo|muevo|asigno)|"
    r"voy a (actualizar|guardar|escribir|crear|documentar|reclasificar|clasificar|"
    r"modificar|cambiar|reorganizar|mover|asignar)|"
    r"procedo a (actualizar|guardar|escribir|reclasificar|clasificar|modificar)|"
    r"actualizo\s+(\*\*)?(opm|pds|pdt|cvv|clv)-|"
    r"(actualizando|reclasificando|clasificando|modificando|reorganizando|"
    r"asignando)\s+(el |la |los |las |cada |todas? )"
    r")"
)
# Se evalúa para cualquier L2 con write_enabled (no solo PDF/metodologías): un
# "hazlo"/"adelante" del usuario tras intención de escritura es la misma señal
# en cualquier dominio, y restringirlo a 2 perfiles dejaba sin nudge al resto
# (bug real: se reportó en agent_professional_identity).

_PDF_PERSIST_NUDGE = (
    "Eso quedó solo en el chat: PostgreSQL no se actualizó. "
    "Si el usuario pidió generar o guardar, llama ahora `pdf_style` o `pdf_template` "
    "con action=update (o create) y el contenido. "
    "Para la guía de clases usa action=update, style_id y style_guide con el Markdown. "
    "No afirmes que ya lo guardaste hasta que la tool devuelva el id."
)
_METHODOLOGIES_PERSIST_NUDGE = (
    "Eso quedó solo en el chat: PostgreSQL no se actualizó. "
    "Llama ahora update_career_record con resource_key='operational-methodologies', "
    "record_id (ej. opm-57) y fields.content con el Markdown completo. "
    "Si es uno nuevo, create_career_record con title, section y content. "
    "No afirmes que lo guardaste hasta que la tool devuelva el id."
)
_GENERIC_PERSIST_NUDGE = (
    "Eso quedó solo en el chat: PostgreSQL no se actualizó. "
    "Llama ahora create_career_record o update_career_record con resource_key, "
    "record_id si aplica, y fields. Si el cambio afecta varios registros del mismo "
    "resource_key (p.ej. reclasificar todas las X), usa bulk_update_career_record con "
    "resource_key y updates=[{record_id, fields}, ...] en vez de llamar update_career_record "
    "una por una — hazlo ahora, en este turno, no lo anuncies solamente. No afirmes que lo "
    "guardaste hasta que la tool devuelva el id o los ids."
)

# Estancamiento genérico: el turno termina con texto que solo anuncia el
# próximo paso ("voy a...", "ahora voy a...") sin haberlo ejecutado, sin que
# haya un write reivindicado (eso ya lo cubre should_nudge_persist arriba).
# Pasa también en tareas de solo lectura/análisis largas (revisar 69
# registros uno por uno) donde el modelo cumple la tool forzada de la ronda 1
# con una sola llamada y luego se conforma con describir el resto.
_ASSISTANT_PROGRESS_STALL = re.compile(
    r"(?i)(voy a \w+|ahora voy a\b|procedo a \w+|a continuaci[óo]n\b|"
    r"contin[uú]o (con|revisando|obteniendo|analizando)\b)"
)
# Frase del usuario que pide detener/cancelar la tarea en curso — si aparece
# en el mensaje que disparó este turno, no se fuerza a seguir trabajando.
_USER_STOP_INTENT = re.compile(
    r"(?i)\b(det[eé]nte|cancela(r)?|ya no (sigas|contin[uú]es)|no sigas|no contin[uú]es|"
    r"olv[ií]dalo|d[eé]jalo as[ií]|mejor no lo hagas|para de\b|alto\b)"
)
_PROGRESS_STALL_NUDGE = (
    "Te quedaste anunciando el próximo paso sin ejecutarlo. No lo vuelvas a describir: llama "
    "ahora mismo la tool correspondiente y termina la tarea completa en este turno (todos los "
    "registros, no solo el primero). Si necesitas revisar muchos, usa list_career_record con "
    "limit=100 y pagina con skip mientras has_more sea true; si vas a cambiar varios, usa "
    "bulk_update_career_record en una sola llamada. Sigue trabajando hasta terminar o hasta que "
    "de verdad necesites un dato que solo Carlos puede darte."
)

# Cuántas veces por turno se reintenta tras un corte por max_tokens antes de
# rendirse (evita loop infinito si el modelo insiste en un payload gigante).
_MAX_TOKENS_RETRY_BUDGET = 2
_MAX_TOKENS_TRUNCATION_NUDGE = (
    "Tu respuesta anterior se cortó por el límite de tokens de salida antes de terminar — no "
    "llegó ni texto ni una tool call completa, así que no se perdió ni se guardó nada todavía. "
    "Repite la misma acción pero en un lote más chico: si iba a ser una sola llamada con muchos "
    "registros (ej. bulk_update_career_record), pártela en tandas de unos 20-25 items y hazlas "
    "una tras otra en este mismo turno hasta cubrir todos. No expliques el corte, solo continúa."
)


def should_retry_max_tokens(
    stop_reason: str, nudges_used: int, max_retries: int = _MAX_TOKENS_RETRY_BUDGET
) -> bool:
    """True cuando la ronda se cortó por maxTokens antes de producir texto o una
    tool_use completa (Bedrock descarta el bloque de contenido a medio terminar
    entero) y todavía queda cupo de reintentos para este turno. Se llama solo
    cuando ya se confirmó que `result["tool_uses"]` vino vacío."""
    return stop_reason == "max_tokens" and nudges_used < max_retries


def _has_unstopped_progress_claim(text: str) -> bool:
    """True si `text` anuncia una acción futura sin negarla justo antes
    ("no voy a...", "ya no voy a..." no cuentan)."""
    for m in _ASSISTANT_PROGRESS_STALL.finditer(text):
        preceding = text[max(0, m.start() - 12):m.start()].lower()
        if "no " in preceding:
            continue
        return True
    return False


def should_nudge_progress(
    profile_level: int,
    user_message: str,
    assistant_text: str,
    nudges_used: int,
    max_nudges: int = 2,
) -> bool:
    """True cuando el turno terminó en texto que solo anuncia el siguiente
    paso de una tarea (sin reclamar un write — eso lo cubre
    should_nudge_persist), el perfil es un L2 con tools reales, no se agotó
    el cupo de empujones de este turno, y el usuario no pidió detenerse."""
    if profile_level != 2:
        return False
    if nudges_used >= max_nudges:
        return False
    if _USER_STOP_INTENT.search(user_message or ""):
        return False
    text = (assistant_text or "").strip()
    if not text:
        return False
    tail = text[-300:]
    if _has_unstopped_progress_claim(tail):
        return True
    # Termina en ":" (lista/próximo paso anunciado) y es corto: probablemente
    # no alcanzó a ejecutar nada después de anunciarlo.
    return tail.rstrip().endswith(":") and len(text) < 600


def persist_nudge_text(profile_id: str) -> str:
    if profile_id == agent_profiles.AGENT_PDF_DESIGN:
        return _PDF_PERSIST_NUDGE
    if profile_id == agent_profiles.AGENT_METHODOLOGIES:
        return _METHODOLOGIES_PERSIST_NUDGE
    return _GENERIC_PERSIST_NUDGE


def _l2_write_profile_ids() -> set:
    return {p.id for p in agent_profiles.list_profiles() if p.level == 2 and p.write_enabled}


def should_nudge_persist(
    profile_id: str,
    user_message: str,
    affected_resources: List[str],
    already_nudged: bool,
    assistant_text: str = "",
) -> bool:
    """True when an L2 writer ended a turn claiming/being asked to write, with no write."""
    if already_nudged or affected_resources:
        return False
    if profile_id not in _l2_write_profile_ids():
        return False
    head = (assistant_text or "")[:400]
    if _ASSISTANT_WRITE_CLAIM.search(head):
        return True
    text = user_message or ""
    return bool(_USER_WRITE_INTENT.search(text) or _USER_PROCEED.search(text))


def should_nudge_pdf_persist(
    profile_id: str,
    user_message: str,
    affected_resources: List[str],
    already_nudged: bool,
    assistant_text: str = "",
) -> bool:
    """Compat: mismo criterio que should_nudge_persist (histórico: solo PDF)."""
    return should_nudge_persist(
        profile_id, user_message, affected_resources, already_nudged, assistant_text
    )


# ============================================================================
# Solicitud de turno y contexto resuelto
# ============================================================================

@dataclass
class ChatTurnRequest:
    session_id: str                # ID único de la sesión de chat
    message: str                   # Mensaje enviado por el usuario
    chat_surface: str = "contextual"         # "general" | "contextual"
    page_context: Optional[Dict[str, Any]] = None  # Metadatos de la página de origen
    model_id: Optional[str] = None           # Modelo sugerido por el cliente
    agent_profile_id: Optional[str] = None   # Perfil/agente solicitado
    attachments: Optional[List[Dict[str, Any]]] = None  # Adjuntos enviados con el mensaje


@dataclass
class TurnContext:
    system_prompt: str
    tool_specs: List[ToolSpec]
    allowed_tools: set
    caller_section_ids: List[str]
    delegate_ids: List[str]


# ============================================================================
# Enganches hacia módulos que aún no existen (T-086/T-087 y T-090/T-091)
# ============================================================================

def is_write_tool(name: str) -> bool:
    """Misma regla que `tools.is_write_tool` de la API; el catálogo de writes vive en `tools_registry`."""
    return name in tools_registry.WRITE_TOOLS


def invalidation_key(name: str, tool_input: Dict[str, Any], tool_result: Dict[str, Any]) -> Optional[str]:
    """Enganche: lo aporta T-087 (traslado de `tools.invalidation_key`, D-13). Tests: se sustituye."""
    raise NotImplementedError("invalidation_key lo implementa T-087 (services/tools_career.py)")


async def run_specialist_sub_turn(db, *, user_id, session_id, profile, task, context, delegation_depth) -> dict:
    """Enganche: lo implementa T-091 (services/delegation.py). Tests: se sustituye."""
    raise NotImplementedError("run_specialist_sub_turn lo implementa T-091 (services/delegation.py)")


# ============================================================================
# Resolución del perfil del turno (D-10, D-31)
# ============================================================================

def _normalize_path(route: str) -> str:
    return route.split("?")[0].rstrip("/") or "/"


def _match_section(route: str, sections: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Paridad con `admin_sections.match_section`: ruta exacta; si no, el prefijo más largo."""
    if not route:
        return None
    path = _normalize_path(route)
    for item in sections:
        if _normalize_path(item.get("path") or "") == path:
            return item
    prefixed = [i for i in sections if path.startswith(f"{_normalize_path(i.get('path') or '')}/")]
    if not prefixed:
        return None
    return max(prefixed, key=lambda i: len(_normalize_path(i["path"])))


async def _resolve_profile(req: ChatTurnRequest, sections: Optional[SectionsClient]):
    """Paridad con `section_catalog.resolve_profile_for_turn`; las secciones se leen por REST con la
    credencial del llamante. Un fallo de lectura degrada al orquestador y deja un WARNING (D-31)."""
    orchestrator = agent_profiles.AGENT_ORCHESTRATOR
    if req.chat_surface == "general":
        return agent_profiles.get_profile(orchestrator)
    if req.agent_profile_id:
        return agent_profiles.get_profile(req.agent_profile_id)
    route = (req.page_context or {}).get("route") or ""
    if sections is not None and route:
        try:
            items = await sections.list()
        except (httpx.ConnectError, ApiError) as exc:
            logger.warning("No se pudieron leer las secciones (%s); se usa el orquestador", exc)
        else:
            matched = _match_section(route, items)
            if matched and matched.get("agent_profile_id"):
                return agent_profiles.get_profile(matched["agent_profile_id"])
    return agent_profiles.get_profile(orchestrator)


async def resolve_turn_context(
    db: AsyncSession, user_id: str, profile, req: ChatTurnRequest, *, sections: Optional[SectionsClient]
) -> TurnContext:
    """Costura del módulo: prompt de sistema, tools efectivas y delegación, resueltos una vez por turno."""
    overrides = await profile_repo.list_delegation_overrides(db)
    delegate_ids = (
        agent_profiles.filter_level_allowed(profile, overrides[profile.id])
        if profile.id in overrides
        else profile_catalog.default_delegation_ids(profile)
    )
    if sections is not None:
        allowed, caller_section_ids = await profile_catalog.resolve_effective_tools(db, sections, profile)
    else:
        allowed = tools_registry.effective_tool_names(profile, await profile_repo.get_tool_override(db, profile.id))
        caller_section_ids = []
    notes = None
    if profile.user_facing:
        try:
            notes = await memory_service.list_agent_notes(db, user_id, profile.id)
        except Exception:
            logger.warning("No se pudo cargar la memoria propia de %s", profile.id, exc_info=True)
    system_prompt = await prompt.compose_system_prompt(
        db, profile, req.page_context, notes=notes, delegate_ids=delegate_ids
    )
    specs = tools_registry.tool_specs(allowed, caller_profile=profile, delegate_ids=delegate_ids)
    return TurnContext(
        system_prompt=system_prompt,
        tool_specs=specs,
        allowed_tools=set(allowed),
        caller_section_ids=caller_section_ids,
        delegate_ids=delegate_ids,
    )


# ============================================================================
# Resolución de modelo efectivo
# ============================================================================

def _effective_model(req: ChatTurnRequest, runtime, profile, available: set) -> str:
    """Modelo del turno (igual que la API; el catálogo permitido sale de `provider.list_models()`)."""
    weak_models = {"amazon.nova-lite-v1:0"}

    if req.chat_surface == "general":
        if profile.default_model_id and profile.default_model_id in available:
            return profile.default_model_id
        return runtime.orchestrator_model_id

    if req.model_id and req.model_id in available:
        if req.model_id not in weak_models:
            return req.model_id

    if profile.default_model_id and profile.default_model_id in available:
        return profile.default_model_id

    return resolve_recommended_model(req.page_context)


# ============================================================================
# Turno síncrono
# ============================================================================

async def run_single_turn_sync(
    db: AsyncSession,
    *,
    user_id: str,
    session_id: str,
    message: str,
    provider: ModelProvider,
    tool_executor: ToolExecutor,
    sections: Optional[SectionsClient] = None,
    chat_surface: str = "contextual",
    agent_profile_id: Optional[str] = None,
    page_context: Optional[dict] = None,
    model_id: Optional[str] = None,
    max_round_trips: Optional[int] = None,
    record_history: bool = True,
    load_session_history: Optional[bool] = None,
    delegation_depth: int = 0,
) -> Dict[str, Any]:
    """Un turno sin streaming SSE: devuelve el evento `done`; un evento `error` lanza `ProviderError`."""
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
        provider=provider,
        tool_executor=tool_executor,
        sections=sections,
        max_round_trips_override=max_round_trips,
        record_history=record_history,
        load_session_history=load_session_history,
        delegation_depth=delegation_depth,
    ):
        if event["type"] == "done":
            last = event
        elif event["type"] == "error":
            raise ProviderError(event["message"])
    return last


# ============================================================================
# Turno con streaming SSE
# ============================================================================

def _sum_usage(total: Usage, usage: Usage) -> None:
    total.input_tokens += usage.input_tokens
    total.output_tokens += usage.output_tokens
    total.cache_read_tokens += usage.cache_read_tokens
    total.cache_write_tokens += usage.cache_write_tokens


def _has_usage(usage: Usage) -> bool:
    return any((usage.input_tokens, usage.output_tokens, usage.cache_read_tokens, usage.cache_write_tokens))


async def chat_stream(
    db: AsyncSession,
    user_id: str,
    req: ChatTurnRequest,
    *,
    provider: ModelProvider,
    tool_executor: ToolExecutor,
    sections: Optional[SectionsClient] = None,
    max_round_trips_override: Optional[int] = None,
    record_history: bool = True,
    load_session_history: Optional[bool] = None,
    delegation_depth: int = 0,
) -> AsyncIterator[Dict[str, Any]]:
    """Genera los eventos del turno: `status`, `delegation_start/end`, `done`, `error`.

    El presupuesto agotado lanza `usage_service.BudgetExceeded` antes del primer evento; un
    `agent_profile_id` desconocido propaga `KeyError` (como la API).
    """
    # 1. Ajustes de runtime y presupuesto
    runtime = await settings_loader.get_runtime_settings(db)
    await usage_service.assert_budget_available(db, user_id, runtime.daily_budget_usd)

    # 2. Perfil del turno y modelo
    profile = await _resolve_profile(req, sections)
    if profile.level == 3 and record_history:
        yield {
            "type": "error",
            "message": "Los agentes de nivel 3 no tienen chat con el usuario. Delega desde L1 o L2.",
        }
        return
    available = {m.model_id for m in provider.list_models()}
    model_id = _effective_model(req, runtime, profile, available)

    # 3. Prompt, tools y delegación, una vez por turno
    ctx = await resolve_turn_context(db, user_id, profile, req, sections=sections)
    allowed_delegate_ids = ctx.delegate_ids
    caller_section_ids = ctx.caller_section_ids

    # 4. Historial y mensaje del usuario
    session_type = "general" if req.chat_surface == "general" else "contextual"
    include_history = record_history if load_session_history is None else load_session_history
    if include_history:
        history = await conversation_repo.load_converse_messages(db, user_id, req.session_id, runtime.history_window)
    else:
        history = []
    user_content = await build_user_content_blocks(db, user_id, req.message, req.attachments)
    messages = history + [{"role": "user", "content": user_content}]

    # 5. Conversación (solo se guarda el id: un rollback expira el objeto, ver API)
    conversation_id: Optional[str] = None
    if record_history:
        conversation = await conversation_repo.get_or_create_conversation(
            db,
            user_id,
            req.session_id,
            req.message,
            session_type=session_type,
            agent_profile_id=profile.id,
        )
        conversation_id = conversation.id

    # 6. Estado del turno
    affected: List[str] = []
    total_usage = Usage()
    max_rounds = max_round_trips_override or runtime.max_round_trips
    delegations_used = 0
    progress_nudge_count = 0
    max_tokens_nudge_count = 0
    persist_nudge_sent = False
    seen_reads: set = set()

    yield {"type": "status", "message": "Pensando..."}

    force_tool_this_round = True
    for _ in range(max_rounds):
        try:
            result = await provider.converse(
                ModelRequest(
                    model_id=model_id,
                    messages=messages,
                    system_prompt=ctx.system_prompt,
                    tools=ctx.tool_specs,
                    max_tokens=settings.BEDROCK_MAX_OUTPUT_TOKENS,
                    force_tool_use=force_tool_this_round and bool(ctx.tool_specs),
                )
            )
        except ProviderError as e:
            if _has_usage(total_usage):
                await usage_service.record_turn_usage(user_id, req.session_id, model_id, total_usage)
            yield {"type": "error", "message": str(e)}
            return
        force_tool_this_round = False

        _sum_usage(total_usage, result.usage)
        await usage_service.record_round_log(
            user_id=user_id,
            session_id=req.session_id,
            model_id=model_id,
            round_type="converse",
            usage=result.usage,
            agent_profile_id=profile.id,
        )

        # Sin tool_calls utilizables no hay respuesta final todavía si hubo corte/nudge
        if not result.tool_calls:
            if should_retry_max_tokens(result.stop_reason, max_tokens_nudge_count):
                max_tokens_nudge_count += 1
                force_tool_this_round = True
                yield {"type": "status", "message": "La respuesta se cortó por límite de tokens; reintentando en tandas más pequeñas..."}
                messages.extend(
                    [
                        {"role": "assistant", "content": [{"text": result.text or "(sin texto)"}]},
                        {"role": "user", "content": [{"text": _MAX_TOKENS_TRUNCATION_NUDGE}]},
                    ]
                )
                continue
            if should_nudge_persist(profile.id, req.message, affected, persist_nudge_sent, result.text or ""):
                persist_nudge_sent = True
                force_tool_this_round = True
                yield {"type": "status", "message": "Persistiendo el contenido en la base de datos..."}
                messages.extend(
                    [
                        {"role": "assistant", "content": [{"text": result.text or "(sin texto)"}]},
                        {"role": "user", "content": [{"text": persist_nudge_text(profile.id)}]},
                    ]
                )
                continue
            if should_nudge_progress(profile.level, req.message, result.text or "", progress_nudge_count):
                progress_nudge_count += 1
                force_tool_this_round = True
                yield {"type": "status", "message": "Continuando la tarea..."}
                messages.extend(
                    [
                        {"role": "assistant", "content": [{"text": result.text or "(sin texto)"}]},
                        {"role": "user", "content": [{"text": _PROGRESS_STALL_NUDGE}]},
                    ]
                )
                continue
            await usage_service.record_turn_usage(user_id, req.session_id, model_id, total_usage)
            # Converse rechaza bloques de texto vacíos: placeholder para mantener válido el historial.
            final_reply = result.text or "(sin texto)"
            if record_history and conversation_id:
                await conversation_repo.append_message(db, conversation_id, "user", req.message or "(sin texto)")
                await conversation_repo.append_message(db, conversation_id, "assistant", final_reply)
            yield {"type": "done", "reply": final_reply, "affected_resources": affected}
            return

        # Ejecución de tools
        for t in result.tool_calls:
            yield {"type": "status", "message": _TOOL_STATUS.get(t.name, f"Usando {t.name}...")}

        assistant_content = [
            {"toolUse": {"toolUseId": t.id, "name": t.name, "input": t.input}} for t in result.tool_calls
        ]
        tool_result_content = []

        for t in result.tool_calls:
            name = t.name
            try:
                status = "success"
                if name == "delegate_to_specialist":
                    spec_id = t.input.get("agent_profile_id", "")
                    deny = None
                    if not profile.can_delegate:
                        deny = "this profile cannot delegate"
                    elif delegation_depth >= 2:
                        deny = "max delegation depth exceeded"
                    elif delegations_used >= settings.BEDROCK_MAX_DELEGATIONS_PER_TURN:
                        deny = "max delegations per turn exceeded"
                    else:
                        deny = agent_profiles.delegation_error(
                            profile, spec_id, allowed_ids=set(allowed_delegate_ids)
                        )
                    if deny:
                        tool_result = {"error": deny}
                        status = "error"
                    else:
                        try:
                            target = agent_profiles.get_profile(spec_id)
                        except KeyError:
                            tool_result = {"error": f"unknown agent profile: {spec_id}"}
                            status = "error"
                        else:
                            yield {
                                "type": "delegation_start",
                                "agent_profile_id": spec_id,
                                "label": target.label,
                                "level": target.level,
                                "task_preview": (t.input.get("task") or "")[:120],
                            }
                            sub = await run_specialist_sub_turn(
                                db,
                                user_id=user_id,
                                session_id=req.session_id,
                                profile=target,
                                task=t.input.get("task", ""),
                                context=t.input.get("context"),
                                delegation_depth=delegation_depth,
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
                    dedup_key = (
                        f"{name}:{json.dumps(t.input, sort_keys=True, ensure_ascii=False)}"
                        if name in _DEDUP_READ_TOOLS
                        else None
                    )
                    if t.input_parse_error:
                        tool_result = {"error": t.input_parse_error}
                        status = "error"
                    elif dedup_key is not None and dedup_key in seen_reads:
                        tool_result = {
                            "note": (
                                "Idéntico a una llamada previa en este mismo turno. "
                                "Reutiliza aquel resultado; no lo vuelvas a pedir."
                            )
                        }
                        status = "success"
                    else:
                        tool_result = await tool_executor(
                            db, user_id, name, t.input, req.session_id,
                            caller_profile_id=profile.id,
                            caller_section_ids=caller_section_ids,
                        )
                        status = "success"
                        if dedup_key is not None:
                            seen_reads.add(dedup_key)
                if name == "delegate_to_specialist" and isinstance(tool_result, dict):
                    for key in tool_result.get("affected_resources") or []:
                        if key not in affected:
                            affected.append(key)
                inv_key = invalidation_key(name, t.input, tool_result)
                if inv_key and inv_key not in affected:
                    affected.append(inv_key)
                # Un write (directo o vía delegación) invalida las lecturas deduplicadas del turno.
                _wrote = (
                    is_write_tool(name)
                    and not (isinstance(tool_result, dict) and tool_result.get("error"))
                ) or (
                    name == "delegate_to_specialist"
                    and isinstance(tool_result, dict)
                    and tool_result.get("affected_resources")
                )
                if _wrote:
                    seen_reads.clear()
            except Exception as e:
                # Un fallo de flush deja la sesión en "pending rollback": sin rollback, cualquier
                # tool posterior del mismo turno revienta con un error genérico que oculta la causa.
                try:
                    await db.rollback()
                except Exception:
                    logger.exception("db.rollback() falló tras error en tool %s", name)
                tool_result = {"error": str(e)}
                status = "error"

            tool_result_content.append({
                "toolResult": {
                    "toolUseId": t.id,
                    "content": [{"text": json.dumps(tool_result, ensure_ascii=False, default=str)}],
                    "status": status,
                }
            })

        messages.extend([
            {"role": "assistant", "content": assistant_content},
            {"role": "user", "content": tool_result_content},
        ])

    await usage_service.record_turn_usage(user_id, req.session_id, model_id, total_usage)
    yield {"type": "error", "message": "Se agotaron las vueltas del agente sin respuesta final."}
