"""RF-005 / RF-004 / D-26: bucle de agente (`services/agent_loop.py`, T-085) con un `FakeProvider`.

T-084 escribe estos tests en ROJO: `services.agent_loop` aún no existe. Se importa de forma
perezosa (fixture `loop`) para que cada test falle por `ModuleNotFoundError` sin romper la
recolección del resto de la suite.

INTERFAZ QUE T-085 DEBE CUMPLIR (traslado de `cjhirashi-career-api/src/services/bedrock/agent_loop.py`,
adaptado al Protocol `ModelProvider`)
-----------------------------------------------------------------------------------------------
Decidido: `agent_loop` usa `provider.converse()` (una llamada por ida y vuelta, como la API con
`converse_client.converse`), NO `converse_stream`. Hereda así el respaldo a Converse ante
`AccessDeniedException` que ya tiene `BedrockProvider.converse`; sin cambio en el Protocol.

    @dataclass ChatTurnRequest(session_id, message, chat_surface="contextual", page_context=None,
                               model_id=None, agent_profile_id=None, attachments=None)

    @dataclass TurnContext(system_prompt: str, tool_specs: list[ToolSpec], allowed_tools: set[str],
                           caller_section_ids: list[str], delegate_ids: list[str])

    async def resolve_turn_context(db, user_id, profile, req, *, sections) -> TurnContext
        Costura del módulo: resuelve en UN sitio el prompt de sistema (`prompt.compose_system_prompt`),
        las tools efectivas (`profile_catalog.resolve_effective_tools` + `tools_registry.tool_specs`)
        y la delegación. Los tests la sustituyen con `monkeypatch.setattr(agent_loop, ...)`.

    async def chat_stream(db, user_id, req, *, provider, tool_executor, sections=None,
                          max_round_trips_override=None, record_history=True,
                          load_session_history=None, delegation_depth=0) -> AsyncIterator[dict]
        - `provider`: `ModelProvider` inyectado (nunca instancia el cliente AWS; sólo `.converse()`
          y `.list_models()`; `estimate_cost` lo usa `usage_service`).
        - `tool_executor`: `async (db, user_id, name, tool_input, session_id, *, caller_profile_id,
          caller_section_ids) -> Any` (misma firma que `tools.execute_tool` de la API).
        - Eventos (iguales a la API): {"type":"status","message"}, {"type":"done","reply",
          "affected_resources"}, {"type":"error","message"} (delegation_* fuera de este test).
        - Un `ProviderError` del provider -> evento error con `str(e)`; el presupuesto agotado lanza
          `usage_service.BudgetExceeded` ANTES del primer evento y sin llamar al provider.
        - El mensaje de usuario se construye con `build_user_content_blocks` (ver abajo).
        - El perfil del turno se resuelve DENTRO del bucle, con paridad con la API
          (`section_catalog.resolve_profile_for_turn`, D-10): `general` -> orquestador L1; `contextual` con
          `agent_profile_id` -> ese perfil; sin override, se busca la sección de `page_context["route"]`
          (ruta exacta y, si no, el prefijo más largo; se ignoran `?query` y la barra final) y se usa su
          `agent_profile_id`; sección sin agente, ruta sin sección, `sections=None` o fallo de `sections`
          -> orquestador. La sección MÁS ESPECÍFICA decide (como `match_section`): si `/networking/x` no
          tiene agente, el turno va al orquestador aunque `/networking` sí lo tenga. La ruta raíz `/` casa
          sólo con la sección de path `/`. Un `agent_profile_id` inexistente (de la sección o del override)
          hace que `agent_profiles.get_profile` lance `KeyError`, que SE PROPAGA fuera de `chat_stream`
          (antes del primer evento, sin llamar al provider): mismo comportamiento que la API, que no la captura.
          D-31 (usuario, spec.md): si la lectura REST de secciones falla (red, `ApiError` 401/403/5xx) el
          turno degrada al orquestador y registra un `logging.warning` con la causa; no corta el turno. En el harness no hay BD de secciones: T-085 lee las secciones con el
          cliente inyectado `sections` (`clients.sections.SectionsClient.list()`, REST `/admin/sections`,
          que devuelve dicts con `id`, `path` y `agent_profile_id` efectivo) y hace la coincidencia por
          `path`. NO se usa `agent_profiles.resolve_agent_profile` (mapa estático ruta->perfil): es otra
          semántica. Los perfiles se obtienen de `agent_profiles.get_profile`.

    async def run_single_turn_sync(db, *, user_id, session_id, message, provider, tool_executor, ...)
        -> dict   (último evento "done"; lanza `ProviderError` ante un evento "error")

Colaboradores que el bucle DEBE llamar por atributo de módulo (así los tests los sustituyen):
    settings_loader.get_runtime_settings(db)        usage_service.assert_budget_available/record_*
    conversation_repo.get_or_create_conversation / append_message / load_converse_messages
    agent_profiles.get_profile                       (el perfil sale de `sections`, ver arriba)

Funciones y nombres de módulo que `agent_loop` DEBE exponer (traslado literal de la API, mismos textos y regex):
    should_retry_max_tokens(stop_reason, nudges_used, max_retries=2) -> bool
    should_nudge_persist(profile_id, user_message, affected_resources, already_nudged, assistant_text="") -> bool
    should_nudge_pdf_persist(...)  (compat: mismo criterio)       persist_nudge_text(profile_id) -> str
    should_nudge_progress(profile_level, user_message, assistant_text, nudges_used, max_nudges=2) -> bool
    build_user_content_blocks(db, user_id, message, attachments) -> list[dict]
        El bucle usa `attachments.build_user_content_blocks` (`services/attachments.py`, T-084a/T-084b) y lo
        expone como atributo de módulo `agent_loop.build_user_content_blocks` (sin adjuntos:
        [{"text": message}]; con adjuntos: texto + bloques image/document). Aquí se sustituye por un doble.
    resolve_recommended_model(page_context) -> str
        El bucle usa `section_profiles.resolve_recommended_model` (`services/section_profiles.py`,
        T-084c/T-084d), expuesto como atributo `agent_loop.resolve_recommended_model` (último recurso de la
        elección de modelo). Aquí se sustituye por un doble.
    invalidation_key(name, tool_input, tool_result) -> Optional[str]   y   is_write_tool(name) -> bool
        (api `tools.py`; los aportan T-086/T-087 y el bucle los expone como atributos de módulo.)
    run_specialist_sub_turn(db, *, user_id, session_id, profile, task, context, delegation_depth) -> dict
        (gancho de delegación; su implementación es T-090/T-091, aquí sólo el enganche.)
    config.Settings.BEDROCK_MAX_DELEGATIONS_PER_TURN: int = 3  (T-085 lo añade; hoy sólo existe en la API)
    max_tokens de la petición = `config.settings.BEDROCK_MAX_OUTPUT_TOKENS` (leído en cada turno).

Adaptaciones al Protocol (frente a la API): `ModelResponse.tool_calls` (no `tool_uses`: `.id`, `.name`,
`.input`, `.input_parse_error`) y `Usage` en snake_case (no `inputTokens`); el modelo permitido se
valida contra `provider.list_models()` (en la API era `settings.BEDROCK_AVAILABLE_MODELS`).
La credencial hacia la API (RF-004) NO viaja por parámetro: el bucle ejecuta las tools en el contexto
del llamador (`Principal` o `ServiceContext` en `contextvars`) y `ApiClient` la toma de ahí.
"""
import copy
import importlib
import json
from contextlib import asynccontextmanager
from types import SimpleNamespace
from typing import Any, AsyncIterator, List

import httpx
import pytest
from botocore.exceptions import ClientError

from clients.api_client import ApiClient, ApiError
from middleware.principal import Principal, ServiceContext, principal_scope, service_scope
from providers.base import (
    ImageOptions,
    ImageResult,
    ModelInfo,
    ModelProvider,
    ModelRequest,
    ModelResponse,
    ProviderError,
    StreamEvent,
    ToolCall,
    ToolSpec,
    Usage,
)

# Textos exactos de la API (api:105-163), copiados literalmente: son el contrato con el modelo.
PDF_PERSIST_NUDGE = 'Eso quedó solo en el chat: PostgreSQL no se actualizó. Si el usuario pidió generar o guardar, llama ahora `pdf_style` o `pdf_template` con action=update (o create) y el contenido. Para la guía de clases usa action=update, style_id y style_guide con el Markdown. No afirmes que ya lo guardaste hasta que la tool devuelva el id.'
METHODOLOGIES_PERSIST_NUDGE = "Eso quedó solo en el chat: PostgreSQL no se actualizó. Llama ahora update_career_record con resource_key='operational-methodologies', record_id (ej. opm-57) y fields.content con el Markdown completo. Si es uno nuevo, create_career_record con title, section y content. No afirmes que lo guardaste hasta que la tool devuelva el id."
GENERIC_PERSIST_NUDGE = 'Eso quedó solo en el chat: PostgreSQL no se actualizó. Llama ahora create_career_record o update_career_record con resource_key, record_id si aplica, y fields. Si el cambio afecta varios registros del mismo resource_key (p.ej. reclasificar todas las X), usa bulk_update_career_record con resource_key y updates=[{record_id, fields}, ...] en vez de llamar update_career_record una por una — hazlo ahora, en este turno, no lo anuncies solamente. No afirmes que lo guardaste hasta que la tool devuelva el id o los ids.'
PROGRESS_STALL_NUDGE = 'Te quedaste anunciando el próximo paso sin ejecutarlo. No lo vuelvas a describir: llama ahora mismo la tool correspondiente y termina la tarea completa en este turno (todos los registros, no solo el primero). Si necesitas revisar muchos, usa list_career_record con limit=100 y pagina con skip mientras has_more sea true; si vas a cambiar varios, usa bulk_update_career_record en una sola llamada. Sigue trabajando hasta terminar o hasta que de verdad necesites un dato que solo Carlos puede darte.'
MAX_TOKENS_TRUNCATION_NUDGE = 'Tu respuesta anterior se cortó por el límite de tokens de salida antes de terminar — no llegó ni texto ni una tool call completa, así que no se perdió ni se guardó nada todavía. Repite la misma acción pero en un lote más chico: si iba a ser una sola llamada con muchos registros (ej. bulk_update_career_record), pártela en tandas de unos 20-25 items y hazlas una tras otra en este mismo turno hasta cubrir todos. No expliques el corte, solo continúa.'

NOVA = "amazon.nova-lite-v1:0"
HAIKU = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
SONNET = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
RUNTIME_MODEL = "fake.orchestrator-model"
LIST_TOOL = ToolSpec(
    name="list_career_record",
    description="lista registros",
    input_schema={"type": "object", "properties": {"resource_key": {"type": "string"}}},
)
GET_TOOL = ToolSpec(
    name="get_career_record",
    description="lee un registro",
    input_schema={"type": "object", "properties": {"resource_key": {"type": "string"}}},
)


# ---------------------------------------------------------------------------------------------
# Dobles
# ---------------------------------------------------------------------------------------------

class FakeProvider:
    """`ModelProvider` guionado: devuelve (o lanza) una respuesta por llamada a `converse`.

    `converse_stream` falla si el bucle lo usa (decisión: el bucle usa `converse()`).
    El coste es determinista: 0.001/entrada, 0.002/salida, 0.0001/lectura de caché, 0.0005/escritura.
    """

    def __init__(self, script: List[Any], models: Any = None):
        self.script = list(script)
        self.models = models  # ids que lista el catálogo (None = Haiku, Sonnet y Nova)
        self.requests: List[ModelRequest] = []
        self.stream_calls = 0

    async def converse(self, request: ModelRequest) -> ModelResponse:
        # El bucle muta `messages` entre rondas: se guarda una copia del instante de la llamada.
        self.requests.append(
            ModelRequest(
                model_id=request.model_id,
                messages=copy.deepcopy(request.messages),
                system_prompt=request.system_prompt,
                tools=list(request.tools),
                max_tokens=request.max_tokens,
                force_tool_use=request.force_tool_use,
            )
        )
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    def converse_stream(self, request: ModelRequest) -> AsyncIterator[StreamEvent]:
        self.stream_calls += 1
        raise AssertionError("agent_loop debe usar provider.converse(), no converse_stream()")

    async def generate_image(self, prompt: str, options: ImageOptions) -> ImageResult:
        return ImageResult(data=b"")

    def list_models(self) -> List[ModelInfo]:
        catalog = [
            ModelInfo(model_id=HAIKU, label="Haiku", tier="standard"),
            ModelInfo(model_id=SONNET, label="Sonnet", tier="premium"),
            ModelInfo(model_id=NOVA, label="Nova Lite", tier="economy"),
        ]
        return [m for m in catalog if self.models is None or m.model_id in self.models]

    def estimate_cost(self, model_id: str, usage: Usage) -> float:
        return round(
            usage.input_tokens * 0.001
            + usage.output_tokens * 0.002
            + usage.cache_read_tokens * 0.0001
            + usage.cache_write_tokens * 0.0005,
            6,
        )


def text_reply(text="Hola Carlos", usage=None, stop="end_turn") -> ModelResponse:
    return ModelResponse(text=text, stop_reason=stop, usage=usage or Usage(input_tokens=10, output_tokens=5))


def tool_reply(*calls: ToolCall, usage=None, text="") -> ModelResponse:
    return ModelResponse(
        text=text, stop_reason="tool_use", usage=usage or Usage(input_tokens=10, output_tokens=5), tool_calls=list(calls)
    )


WRITE_NAMES = {"update_career_record", "create_career_record", "delete_career_record"}
UPDATE_TOOL = ToolSpec(name="update_career_record", description="actualiza", input_schema={"type": "object"})


class FakeDb:
    def __init__(self):
        self.rollbacks = 0

    async def rollback(self):
        self.rollbacks += 1


class Recorder:
    """Ejecutor de tools guionado; registra cada llamada."""

    def __init__(self, results=None, fail=None):
        self.calls = []
        self.results = results or {}
        self.fail = fail or {}

    async def __call__(self, db, user_id, name, tool_input, session_id, *, caller_profile_id, caller_section_ids):
        self.calls.append(
            {
                "user_id": user_id,
                "name": name,
                "input": tool_input,
                "session_id": session_id,
                "caller_profile_id": caller_profile_id,
                "caller_section_ids": caller_section_ids,
            }
        )
        if name in self.fail:
            raise self.fail[name]
        return self.results.get(json.dumps([name, tool_input], sort_keys=True), {"ok": True})


class Env:
    """Estado observable del entorno simulado (BD, uso, historial)."""

    def __init__(self):
        self.turn_logs: List[dict] = []
        self.round_logs: List[dict] = []
        self.history_rows: List[tuple] = []  # (role, text) ya persistidos antes del turno
        self.load_args: List[tuple] = []
        self.created: List[dict] = []
        self.appended: List[tuple] = []
        self.context_args: List[dict] = []
        self.spend = 0.0
        self.settings = dict(max_round_trips=6, history_window=20, daily_budget_usd=5.0)
        self.tool_specs: List[ToolSpec] = []
        self.system_prompt = "SYS"
        self.delegate_ids: List[str] = []
        self.content_calls: List[tuple] = []
        self.sub_turns: List[dict] = []
        self.sub_result: dict = {"summary": "hecho", "affected_resources": []}
        self.recommended_calls: List[Any] = []


@pytest.fixture
def loop():
    """Importa `services.agent_loop` de forma perezosa: rojo = ModuleNotFoundError (T-085 pendiente)."""
    return importlib.import_module("services.agent_loop")


@pytest.fixture
def env(monkeypatch, loop):
    import services.usage_service as usage_service
    from repositories import conversation_repo, settings_repo, usage_repo

    e = Env()

    async def get_settings(db):
        return SimpleNamespace(
            active_model_id=HAIKU,
            orchestrator_model_id=RUNTIME_MODEL,
            max_round_trips=e.settings["max_round_trips"],
            history_window=e.settings["history_window"],
            daily_budget_usd=e.settings["daily_budget_usd"],
        )

    async def get_daily_spend_usd(db, user_id):
        return e.spend

    async def add_turn_log(db, **kw):
        e.turn_logs.append(kw)

    async def add_round_log(db, **kw):
        e.round_logs.append(kw)

    @asynccontextmanager
    async def session_factory():
        yield FakeDb()

    async def get_or_create_conversation(db, user_id, session_id, first_message, session_type="contextual",
                                         agent_profile_id=None):
        e.created.append(dict(user_id=user_id, session_id=session_id, first_message=first_message,
                              session_type=session_type, agent_profile_id=agent_profile_id))
        return SimpleNamespace(id="conv-1")

    async def append_message(db, conversation_id, role, content):
        e.appended.append((conversation_id, role, content))

    async def load_converse_messages(db, user_id, session_id, window):
        # Misma semántica que el repositorio real: los últimos `window` mensajes (0 = todos).
        e.load_args.append((user_id, session_id, window))
        rows = e.history_rows[-window:] if window else e.history_rows
        return [{"role": role, "content": [{"text": text}]} for role, text in rows]

    async def resolve_turn_context(db, user_id, profile, req, *, sections):
        e.context_args.append(dict(user_id=user_id, profile_id=profile.id, sections=sections))
        return loop.TurnContext(
            system_prompt=e.system_prompt,
            tool_specs=list(e.tool_specs),
            allowed_tools={t.name for t in e.tool_specs},
            caller_section_ids=["sec-1"],
            delegate_ids=list(e.delegate_ids),
        )

    monkeypatch.setattr(settings_repo, "get_settings", get_settings)
    monkeypatch.setattr(usage_repo, "get_daily_spend_usd", get_daily_spend_usd)
    monkeypatch.setattr(usage_repo, "add_turn_log", add_turn_log)
    monkeypatch.setattr(usage_repo, "add_round_log", add_round_log)
    monkeypatch.setattr(usage_service, "_default_session_factory", session_factory)
    monkeypatch.setattr(conversation_repo, "get_or_create_conversation", get_or_create_conversation)
    monkeypatch.setattr(conversation_repo, "append_message", append_message)
    monkeypatch.setattr(conversation_repo, "load_converse_messages", load_converse_messages)
    async def build_user_content_blocks(db, user_id, message, attachments):
        e.content_calls.append((user_id, message, attachments))
        if not attachments:
            return [{"text": message}]
        return [{"text": f"{message}\n\n[Adjunto: foto.png] (imagen incluida)"},
                {"image": {"format": "png", "source": {"bytes": b"PNG"}}}]

    def invalidation_key(name, tool_input, tool_result):  # doble mínimo de api tools.py (sólo writes)
        if name not in WRITE_NAMES or tool_result.get("error"):
            return None
        return str(tool_input["resource_key"]) if tool_input.get("resource_key") else None

    async def run_specialist_sub_turn(db, *, user_id, session_id, profile, task, context, delegation_depth):
        e.sub_turns.append(dict(user_id=user_id, session_id=session_id, profile_id=profile.id, task=task,
                                context=context, delegation_depth=delegation_depth))
        return e.sub_result

    monkeypatch.setattr(loop, "resolve_turn_context", resolve_turn_context)
    monkeypatch.setattr(loop, "build_user_content_blocks", build_user_content_blocks)
    monkeypatch.setattr(loop, "invalidation_key", invalidation_key)
    monkeypatch.setattr(loop, "is_write_tool", lambda name: name in WRITE_NAMES)
    monkeypatch.setattr(loop, "resolve_recommended_model", lambda page_context: (
        e.recommended_calls.append(page_context) or SONNET))
    monkeypatch.setattr(loop, "run_specialist_sub_turn", run_specialist_sub_turn)
    return e


@pytest.fixture
def priced(monkeypatch):
    """`usage_service` estima el coste con el provider de la fábrica; aquí, el FakeProvider del test."""
    import services.usage_service as usage_service

    def install(provider):
        monkeypatch.setattr(usage_service, "_provider", lambda: provider)

    return install


async def run(loop, provider, tool_executor=None, *, message="hola", surface="general", **kw):
    db = kw.pop("db", None) or FakeDb()
    req = loop.ChatTurnRequest(session_id="s1", message=message, chat_surface=surface,
                               **kw.pop("req_kw", {}))
    events = []
    async for ev in loop.chat_stream(
        db, "u1", req, provider=provider, tool_executor=tool_executor or Recorder(), **kw
    ):
        events.append(ev)
    return events


# ---------------------------------------------------------------------------------------------
# Turno sin tools
# ---------------------------------------------------------------------------------------------

@pytest.mark.requisito("RF-005")
async def test_fake_provider_satisfies_protocol():
    assert isinstance(FakeProvider([]), ModelProvider)


@pytest.mark.requisito("RF-005")
async def test_turn_without_tools_returns_reply_and_sends_expected_request(env, priced, loop):
    provider = FakeProvider([text_reply("Hola Carlos", Usage(input_tokens=10, output_tokens=5))])
    priced(provider)

    events = await run(loop, provider, message="hola")

    assert events == [
        {"type": "status", "message": "Pensando..."},
        {"type": "done", "reply": "Hola Carlos", "affected_resources": []},
    ]
    assert len(provider.requests) == 1
    req = provider.requests[0]
    assert req.model_id == HAIKU  # general + orquestador: su default, permitido por provider.list_models()
    assert req.system_prompt == "SYS"
    assert req.messages == [{"role": "user", "content": [{"text": "hola"}]}]
    assert req.tools == []
    assert req.max_tokens == 8192  # default de settings.BEDROCK_MAX_OUTPUT_TOKENS
    assert req.force_tool_use is False  # sin tools no se fuerza
    assert provider.stream_calls == 0


@pytest.mark.requisito("RF-005")
async def test_empty_model_text_is_replaced_by_placeholder(env, priced, loop):
    provider = FakeProvider([text_reply("")])
    priced(provider)
    events = await run(loop, provider)
    assert events[-1] == {"type": "done", "reply": "(sin texto)", "affected_resources": []}
    assert env.appended == [("conv-1", "user", "hola"), ("conv-1", "assistant", "(sin texto)")]


@pytest.mark.requisito("RF-005")
async def test_model_choice_validates_against_provider_catalog(env, priced, loop):
    provider = FakeProvider([text_reply(), text_reply()])
    priced(provider)
    # Contextual + modelo pedido y listado por el provider -> se respeta.
    await run(loop, provider, surface="contextual", req_kw=dict(model_id=SONNET, agent_profile_id="agent_orchestrator"))
    # Contextual + modelo desconocido -> default del perfil (Haiku).
    await run(loop, provider, surface="contextual", req_kw=dict(model_id="otro.modelo-v1", agent_profile_id="agent_orchestrator"))
    assert [r.model_id for r in provider.requests] == [SONNET, HAIKU]


# ---------------------------------------------------------------------------------------------
# Turno con tool
# ---------------------------------------------------------------------------------------------

@pytest.mark.requisito("RF-005")
async def test_turn_with_tool_executes_it_and_feeds_the_result_back(env, priced, loop):
    env.tool_specs = [LIST_TOOL]
    call = ToolCall(id="tu-1", name="list_career_record", input={"resource_key": "jobs"})
    result = {"items": [{"id": "j1", "title": "Ingeniero"}], "has_more": False}
    executor = Recorder(results={json.dumps(["list_career_record", {"resource_key": "jobs"}], sort_keys=True): result})
    provider = FakeProvider([
        tool_reply(call, usage=Usage(input_tokens=100, output_tokens=20)),
        text_reply("Tienes 1 vacante", Usage(input_tokens=150, output_tokens=30)),
    ])
    priced(provider)

    events = await run(loop, provider, executor, message="lista mis vacantes")

    assert events == [
        {"type": "status", "message": "Pensando..."},
        {"type": "status", "message": "Buscando registros..."},
        {"type": "done", "reply": "Tienes 1 vacante", "affected_resources": []},
    ]
    assert executor.calls == [{
        "user_id": "u1", "name": "list_career_record", "input": {"resource_key": "jobs"},
        "session_id": "s1", "caller_profile_id": "agent_orchestrator", "caller_section_ids": ["sec-1"],
    }]
    first, second = provider.requests
    assert first.tools == [LIST_TOOL] and first.force_tool_use is True  # primera ronda con tools: forzada
    assert second.force_tool_use is False
    assert second.messages == [
        {"role": "user", "content": [{"text": "lista mis vacantes"}]},
        {"role": "assistant", "content": [
            {"toolUse": {"toolUseId": "tu-1", "name": "list_career_record", "input": {"resource_key": "jobs"}}}]},
        {"role": "user", "content": [
            {"toolResult": {"toolUseId": "tu-1", "content": [{"text": json.dumps(result, ensure_ascii=False)}],
                            "status": "success"}}]},
    ]


@pytest.mark.requisito("RF-005")
async def test_tool_failure_becomes_error_result_and_rolls_back_the_session(env, priced, loop):
    env.tool_specs = [GET_TOOL]
    call = ToolCall(id="tu-9", name="get_career_record", input={"resource_key": "jobs"})
    executor = Recorder(fail={"get_career_record": RuntimeError("fallo de la API")})
    provider = FakeProvider([tool_reply(call), text_reply("No pude leerlo")])
    priced(provider)
    db = FakeDb()

    events = await run(loop, provider, executor, db=db)

    assert events[-1]["type"] == "done" and events[-1]["reply"] == "No pude leerlo"
    assert db.rollbacks == 1
    tool_result = provider.requests[1].messages[-1]["content"][0]["toolResult"]
    assert tool_result == {
        "toolUseId": "tu-9",
        "content": [{"text": json.dumps({"error": "fallo de la API"}, ensure_ascii=False)}],
        "status": "error",
    }


@pytest.mark.requisito("RF-005")
async def test_tool_call_with_invalid_json_is_not_executed_and_reports_the_parse_error(env, priced, loop):
    env.tool_specs = [GET_TOOL]
    bad = ToolCall(id="tu-2", name="get_career_record", input={}, input_parse_error="Invalid JSON in tool arguments (x).")
    executor = Recorder()
    provider = FakeProvider([tool_reply(bad), text_reply("ok")])
    priced(provider)

    await run(loop, provider, executor)

    assert executor.calls == []
    tool_result = provider.requests[1].messages[-1]["content"][0]["toolResult"]
    assert tool_result["status"] == "error"
    assert tool_result["content"] == [{"text": json.dumps({"error": "Invalid JSON in tool arguments (x)."})}]


@pytest.mark.requisito("RF-005")
async def test_identical_read_in_same_turn_is_deduplicated(env, priced, loop):
    env.tool_specs = [GET_TOOL]
    call = lambda i: ToolCall(id=f"tu-{i}", name="get_career_record", input={"resource_key": "jobs", "record_id": "j1"})
    executor = Recorder()
    provider = FakeProvider([tool_reply(call(1)), tool_reply(call(2)), text_reply("listo")])
    priced(provider)

    await run(loop, provider, executor)

    assert [c["name"] for c in executor.calls] == ["get_career_record"]  # la segunda no se reejecuta
    note = json.loads(provider.requests[2].messages[-1]["content"][0]["toolResult"]["content"][0]["text"])
    assert note == {"note": "Idéntico a una llamada previa en este mismo turno. Reutiliza aquel resultado; no lo vuelvas a pedir."}


# ---------------------------------------------------------------------------------------------
# Límite de idas y vueltas
# ---------------------------------------------------------------------------------------------

@pytest.mark.requisito("RF-005")
async def test_max_round_trips_from_settings_stops_the_loop_with_error(env, priced, loop):
    env.settings["max_round_trips"] = 2
    env.tool_specs = [LIST_TOOL]
    mk = lambda i: tool_reply(ToolCall(id=f"tu-{i}", name="list_career_record", input={"resource_key": f"r{i}"}),
                              usage=Usage(input_tokens=10, output_tokens=5))
    provider = FakeProvider([mk(1), mk(2), mk(3)])
    priced(provider)

    events = await run(loop, provider)

    assert len(provider.requests) == 2  # exactamente 2 llamadas al modelo
    assert events[-1] == {"type": "error", "message": "Se agotaron las vueltas del agente sin respuesta final."}
    assert not any(e["type"] == "done" for e in events)
    # El gasto de las 2 rondas se registra aunque el turno no termine.
    assert len(env.turn_logs) == 1
    assert (env.turn_logs[0]["input_tokens"], env.turn_logs[0]["output_tokens"]) == (20, 10)
    assert env.appended == []  # un turno fallido no persiste mensajes


@pytest.mark.requisito("RF-005")
async def test_max_round_trips_override_beats_settings(env, priced, loop):
    env.settings["max_round_trips"] = 5
    env.tool_specs = [LIST_TOOL]
    mk = lambda i: tool_reply(ToolCall(id=f"tu-{i}", name="list_career_record", input={"resource_key": f"r{i}"}))
    provider = FakeProvider([mk(1), mk(2)])
    priced(provider)

    events = await run(loop, provider, max_round_trips_override=1)

    assert len(provider.requests) == 1
    assert events[-1]["type"] == "error"


# ---------------------------------------------------------------------------------------------
# Ventana de historial
# ---------------------------------------------------------------------------------------------

@pytest.mark.requisito("RF-005")
async def test_history_window_limits_loaded_history_and_appends_the_new_message(env, priced, loop):
    env.settings["history_window"] = 4
    env.history_rows = [("user" if i % 2 == 0 else "assistant", f"m{i}") for i in range(6)]
    provider = FakeProvider([text_reply("respuesta")])
    priced(provider)

    await run(loop, provider, message="nuevo")

    assert env.load_args == [("u1", "s1", 4)]
    assert provider.requests[0].messages == [
        {"role": "user", "content": [{"text": "m2"}]},
        {"role": "assistant", "content": [{"text": "m3"}]},
        {"role": "user", "content": [{"text": "m4"}]},
        {"role": "assistant", "content": [{"text": "m5"}]},
        {"role": "user", "content": [{"text": "nuevo"}]},
    ]


@pytest.mark.requisito("RF-005")
async def test_sub_turn_without_history_neither_loads_nor_persists(env, priced, loop):
    env.history_rows = [("user", "viejo")]
    provider = FakeProvider([text_reply("sub")])
    priced(provider)

    await run(loop, provider, record_history=False)

    assert env.load_args == [] and env.created == [] and env.appended == []
    assert provider.requests[0].messages == [{"role": "user", "content": [{"text": "hola"}]}]


@pytest.mark.requisito("RF-005")
async def test_completed_turn_persists_user_and_assistant_messages(env, priced, loop):
    provider = FakeProvider([text_reply("Hola Carlos")])
    priced(provider)

    await run(loop, provider, message="hola", surface="general")

    assert env.created == [dict(user_id="u1", session_id="s1", first_message="hola", session_type="general",
                                agent_profile_id="agent_orchestrator")]
    assert env.appended == [("conv-1", "user", "hola"), ("conv-1", "assistant", "Hola Carlos")]


# ---------------------------------------------------------------------------------------------
# Presupuesto diario
# ---------------------------------------------------------------------------------------------

@pytest.mark.requisito("RF-005")
async def test_exhausted_daily_budget_raises_before_calling_the_model(env, priced, loop):
    import services.usage_service as usage_service

    env.settings["daily_budget_usd"] = 5.0
    env.spend = 5.0
    provider = FakeProvider([text_reply()])
    priced(provider)

    with pytest.raises(usage_service.BudgetExceeded) as exc:
        await run(loop, provider)

    assert "Presupuesto diario agotado ($5.00 / $5.00)" in str(exc.value)
    assert provider.requests == []
    assert env.turn_logs == [] and env.round_logs == []
    assert env.appended == []


@pytest.mark.requisito("RF-005")
async def test_spend_just_below_budget_still_runs(env, priced, loop):
    env.settings["daily_budget_usd"] = 5.0
    env.spend = 4.99
    provider = FakeProvider([text_reply("sigue")])
    priced(provider)

    events = await run(loop, provider)

    assert events[-1]["reply"] == "sigue"
    assert len(provider.requests) == 1


# ---------------------------------------------------------------------------------------------
# Coste registrado
# ---------------------------------------------------------------------------------------------

@pytest.mark.requisito("RF-005")
async def test_turn_and_round_costs_are_recorded_with_concrete_values(env, priced, loop):
    env.tool_specs = [LIST_TOOL]
    u1 = Usage(input_tokens=100, output_tokens=20, cache_write_tokens=10)
    u2 = Usage(input_tokens=150, output_tokens=30, cache_read_tokens=40)
    provider = FakeProvider([
        tool_reply(ToolCall(id="tu-1", name="list_career_record", input={"resource_key": "jobs"}), usage=u1),
        text_reply("fin", u2),
    ])
    priced(provider)

    await run(loop, provider)

    # Una fila por ronda, con el coste de esa ronda.
    assert [(r["round_type"], r["model_id"], r["agent_profile_id"], r["input_tokens"], r["output_tokens"],
             r["cache_read_tokens"], r["cache_write_tokens"], r["estimated_cost_usd"]) for r in env.round_logs] == [
        ("converse", HAIKU, "agent_orchestrator", 100, 20, 0, 10, 0.145),   # 0.1 + 0.04 + 0.005
        ("converse", HAIKU, "agent_orchestrator", 150, 30, 40, 0, 0.214),   # 0.15 + 0.06 + 0.004
    ]
    assert all(r["user_id"] == "u1" and r["session_id"] == "s1" for r in env.round_logs)
    # Una fila por turno, con el total acumulado y su coste.
    assert len(env.turn_logs) == 1
    t = env.turn_logs[0]
    assert (t["user_id"], t["session_id"], t["model_id"]) == ("u1", "s1", HAIKU)
    assert (t["input_tokens"], t["output_tokens"], t["cache_read_tokens"], t["cache_write_tokens"]) == (250, 50, 40, 10)
    assert t["estimated_cost_usd"] == 0.359  # 0.25 + 0.1 + 0.004 + 0.005


@pytest.mark.requisito("RF-005")
async def test_provider_error_reports_error_event_and_records_prior_spend(env, priced, loop):
    env.tool_specs = [LIST_TOOL]
    provider = FakeProvider([
        tool_reply(ToolCall(id="tu-1", name="list_career_record", input={"resource_key": "jobs"}),
                   usage=Usage(input_tokens=100, output_tokens=20)),
        ProviderError("cuota agotada"),
    ])
    priced(provider)

    events = await run(loop, provider)

    assert events[-1] == {"type": "error", "message": "cuota agotada"}
    assert len(env.turn_logs) == 1
    assert (env.turn_logs[0]["input_tokens"], env.turn_logs[0]["estimated_cost_usd"]) == (100, 0.14)
    assert env.appended == []


@pytest.mark.requisito("RF-005")
async def test_first_round_provider_error_records_nothing(env, priced, loop):
    provider = FakeProvider([ProviderError("sin credenciales")])
    priced(provider)
    events = await run(loop, provider)
    assert events[-1] == {"type": "error", "message": "sin credenciales"}
    assert env.turn_logs == [] and env.round_logs == []


@pytest.mark.requisito("RF-005")
async def test_run_single_turn_sync_returns_done_event_and_raises_provider_error(env, priced, loop):
    ok = FakeProvider([text_reply("sincrono")])
    priced(ok)
    done = await loop.run_single_turn_sync(
        FakeDb(), user_id="u1", session_id="s1", message="hola", chat_surface="general",
        provider=ok, tool_executor=Recorder(),
    )
    assert done == {"type": "done", "reply": "sincrono", "affected_resources": []}

    bad = FakeProvider([ProviderError("falló")])
    priced(bad)
    with pytest.raises(ProviderError, match="falló"):
        await loop.run_single_turn_sync(
            FakeDb(), user_id="u1", session_id="s1", message="hola", chat_surface="general",
            provider=bad, tool_executor=Recorder(),
        )


@pytest.mark.requisito("RF-005")
async def test_sections_client_is_passed_to_the_context_resolver(env, priced, loop):
    sections = FakeSections([])
    provider = FakeProvider([text_reply()])
    priced(provider)
    await run(loop, provider, sections=sections)
    assert env.context_args == [dict(user_id="u1", profile_id="agent_orchestrator", sections=sections)]
    assert env.context_args[0]["sections"] is sections


# ---- Resolución del perfil del turno (paridad con section_catalog.resolve_profile_for_turn) ------

SECTIONS = [
    {"id": "sec-7", "path": "/networking", "agent_profile_id": "agent_networking"},
    {"id": "sec-8", "path": "/networking/map", "agent_profile_id": "agent_methodologies"},
    {"id": "sec-9", "path": "/dashboard", "agent_profile_id": None},
    {"id": "sec-10", "path": "/networking/x", "agent_profile_id": None},   # más específica y sin agente
    {"id": "sec-11", "path": "/", "agent_profile_id": "agent_methodologies"},  # raíz
    {"id": "sec-12", "path": "/rota", "agent_profile_id": "agent_inexistente"},
]


class FakeSections:
    """`SectionsClient` doble: `list()` devuelve las secciones del Admin (o lanza)."""

    def __init__(self, items, fail=None):
        self.items = items
        self.fail = fail
        self.list_calls = 0

    async def list(self):
        self.list_calls += 1
        if self.fail:
            raise self.fail
        return list(self.items)


async def resolved_profile(env, loop, priced, *, surface, route=None, override=None, sections="default"):
    provider = FakeProvider([text_reply()])
    priced(provider)
    fake = FakeSections(SECTIONS) if sections == "default" else sections
    req_kw = {}
    if route is not None:
        req_kw["page_context"] = {"route": route}
    if override:
        req_kw["agent_profile_id"] = override
    events = await run(loop, provider, surface=surface, sections=fake, req_kw=req_kw)
    assert events[-1]["type"] == "done"
    return env.context_args[-1]["profile_id"], fake


@pytest.mark.requisito("RF-005")
async def test_general_surface_resolves_the_orchestrator_without_reading_sections(env, priced, loop):
    pid, fake = await resolved_profile(env, loop, priced, surface="general", route="/networking")
    assert pid == "agent_orchestrator"
    assert fake.list_calls == 0


@pytest.mark.requisito("RF-005")
async def test_contextual_override_wins_over_the_route_section(env, priced, loop):
    pid, fake = await resolved_profile(env, loop, priced, surface="contextual", route="/networking",
                                       override="agent_methodologies")
    assert pid == "agent_methodologies"
    assert fake.list_calls == 0


@pytest.mark.requisito("RF-005")
@pytest.mark.parametrize("route,expected", [
    ("/networking", "agent_networking"),                 # ruta exacta
    ("/networking/", "agent_networking"),                # barra final
    ("/networking?tab=1", "agent_networking"),           # query ignorada
    ("/networking/?tab=1", "agent_networking"),          # barra final y query a la vez
    ("/", "agent_methodologies"),                        # raíz (rama `or "/"`)
    ("/?tab=1", "agent_methodologies"),
    ("/networking/c-12", "agent_networking"),            # prefijo
    ("/networking/map", "agent_methodologies"),          # exacta gana al prefijo
    ("/networking/map/zona", "agent_methodologies"),     # prefijo más largo
])
async def test_contextual_route_uses_the_agent_of_the_matched_section(env, priced, loop, route, expected):
    pid, fake = await resolved_profile(env, loop, priced, surface="contextual", route=route)
    assert pid == expected
    assert fake.list_calls == 1


@pytest.mark.requisito("RF-005")
@pytest.mark.parametrize("route", ["/dashboard", "/dashboard/x", "/no-existe", "/networkingx", "/networking/x", "/networking/x/y",
                                   "", None])
async def test_section_without_agent_or_without_match_falls_back_to_the_orchestrator(env, priced, loop, route):
    pid, _ = await resolved_profile(env, loop, priced, surface="contextual", route=route)
    assert pid == "agent_orchestrator"


@pytest.mark.requisito("RF-005")
async def test_contextual_without_sections_client_falls_back_to_the_orchestrator(env, priced, loop):
    pid, _ = await resolved_profile(env, loop, priced, surface="contextual", route="/networking", sections=None)
    assert pid == "agent_orchestrator"


@pytest.mark.requisito("RF-005")
@pytest.mark.parametrize("cause,expected_text", [
    (httpx.ConnectError("sin red"), "sin red"),
    (ApiError(401, "token inválido"), "API 401"),
    (ApiError(403, "prohibido"), "API 403"),
    (ApiError(500, "boom"), "API 500"),
])
async def test_sections_failure_degrades_to_orchestrator_and_logs_a_warning_d31(env, priced, loop, caplog, cause, expected_text):
    import logging

    boom = FakeSections(SECTIONS, fail=cause)
    with caplog.at_level(logging.WARNING):
        pid, fake = await resolved_profile(env, loop, priced, surface="contextual", route="/networking", sections=boom)
    assert pid == "agent_orchestrator"
    assert fake.list_calls == 1
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) == 1
    assert expected_text in warnings[0].getMessage()


@pytest.mark.requisito("RF-005")
@pytest.mark.parametrize("route,override", [("/rota", None), ("/networking", "agent_inexistente")])
async def test_unknown_agent_profile_id_propagates_key_error_like_the_api(env, priced, loop, route, override):
    provider = FakeProvider([text_reply()])
    priced(provider)
    kw = dict(page_context={"route": route})
    if override:
        kw["agent_profile_id"] = override
    with pytest.raises(KeyError, match="Unknown agent profile: agent_inexistente"):
        await run(loop, provider, surface="contextual", sections=FakeSections(SECTIONS), req_kw=kw)
    assert provider.requests == [] and env.created == []




# ---------------------------------------------------------------------------------------------
# RF-004: la credencial del usuario llega al cliente de la API
# ---------------------------------------------------------------------------------------------

def make_api_executor(seen: List[dict]):
    """Ejecutor de tools que llama a la API REST con `ApiClient` (credencial desde el contexto)."""

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append({"path": request.url.path, "authorization": request.headers.get("authorization")})
        return httpx.Response(200, json={"items": [], "path": request.url.path})

    api = ApiClient(base_url="http://api.test", transport=httpx.MockTransport(handler), backoff=0)

    async def execute(db, user_id, name, tool_input, session_id, *, caller_profile_id, caller_section_ids):
        return await api.get_json(f"/career/{tool_input['resource_key']}")

    return execute, api


@pytest.mark.requisito("RF-004")
async def test_user_jwt_reaches_the_api_client_for_every_tool_call(env, priced, loop):
    env.tool_specs = [LIST_TOOL]
    seen: List[dict] = []
    execute, api = make_api_executor(seen)
    provider = FakeProvider([
        tool_reply(
            ToolCall(id="tu-1", name="list_career_record", input={"resource_key": "jobs"}),
            ToolCall(id="tu-2", name="list_career_record", input={"resource_key": "skills"}),
        ),
        text_reply("hecho"),
    ])
    priced(provider)

    with principal_scope(Principal(user_id="u1", token="jwt-del-usuario-abc")):
        events = await run(loop, provider, execute)
    await api.aclose()

    assert events[-1]["reply"] == "hecho"
    assert seen == [
        {"path": "/career/jobs", "authorization": "Bearer jwt-del-usuario-abc"},
        {"path": "/career/skills", "authorization": "Bearer jwt-del-usuario-abc"},
    ]


@pytest.mark.requisito("RF-004")
async def test_scheduled_turn_uses_the_service_account_credential(env, priced, loop):
    env.tool_specs = [LIST_TOOL]
    seen: List[dict] = []
    execute, api = make_api_executor(seen)
    provider = FakeProvider([
        tool_reply(ToolCall(id="tu-1", name="list_career_record", input={"resource_key": "jobs"})),
        text_reply("hecho"),
    ])
    priced(provider)

    with service_scope(ServiceContext(token="svc-token-xyz")):
        await run(loop, provider, execute)
    await api.aclose()

    assert seen == [{"path": "/career/jobs", "authorization": "Bearer svc-token-xyz"}]


@pytest.mark.requisito("RF-004")
async def test_without_any_credential_the_loop_does_not_invent_one(env, priced, loop):
    env.tool_specs = [LIST_TOOL]
    seen: List[dict] = []
    execute, api = make_api_executor(seen)
    provider = FakeProvider([
        tool_reply(ToolCall(id="tu-1", name="list_career_record", input={"resource_key": "jobs"})),
        text_reply("no pude"),
    ])
    priced(provider)

    events = await run(loop, provider, execute)  # sin Principal ni ServiceContext
    await api.aclose()

    assert seen == []  # la API nunca recibió una petición
    result = provider.requests[1].messages[-1]["content"][0]["toolResult"]
    assert result["status"] == "error"
    assert json.loads(result["content"][0]["text"]) == {
        "error": "sin Principal ni ServiceContext: no hay credencial hacia la API"
    }
    assert events[-1]["type"] == "done"


# ---------------------------------------------------------------------------------------------
# Con BedrockProvider real (cliente boto3 stub): respaldo a Converse y D-26
# ---------------------------------------------------------------------------------------------

def client_error(code, message="boom"):
    return ClientError({"Error": {"Code": code, "Message": message}}, "ConverseStream")


class StubRuntimeClient:
    """Cliente boto3 de bedrock-runtime: `converse_stream` y `converse` guionados."""

    def __init__(self, stream_error=None, stream_events=None, converse_responses=None):
        self.stream_error = stream_error
        self.stream_events = list(stream_events or [])
        self.converse_responses = list(converse_responses or [])
        self.calls: List[tuple] = []

    def converse_stream(self, **kwargs):
        self.calls.append(("converse_stream", copy.deepcopy(kwargs)))
        if self.stream_error:
            raise self.stream_error
        return {"stream": iter(self.stream_events.pop(0))}

    def converse(self, **kwargs):
        self.calls.append(("converse", copy.deepcopy(kwargs)))
        return self.converse_responses.pop(0)


def converse_message(content, stop, usage):
    return {"output": {"message": {"role": "assistant", "content": content}}, "stopReason": stop, "usage": usage}


@pytest.fixture
def bedrock_stream_provider(monkeypatch):
    """BedrockProvider con BEDROCK_USE_CONVERSE_STREAM=True que obtiene su cliente por el dict de
    módulo de clientes cacheados (`providers.bedrock.client._clients`), que se limpia antes y después."""
    from providers.bedrock import client as client_mod
    from providers.bedrock.converse import BedrockProvider

    client_mod.reset_clients()
    assert client_mod._clients == {}

    def build(stub):
        monkeypatch.setattr(client_mod, "_build", lambda settings, region: stub)
        settings = SimpleNamespace(
            BEDROCK_REGION="us-east-1", BEDROCK_IMAGE_REGION="us-west-2", BEDROCK_IMAGE_MODEL_ID="img",
            BEDROCK_USE_CONVERSE_STREAM=True, BEDROCK_PROMPT_CACHE_ENABLED=False,
            AWS_ACCESS_KEY_ID="AKIAFAKEFAKEFAKEFAKE", AWS_SECRET_ACCESS_KEY="fake-secret",
        )
        return BedrockProvider(settings)

    yield build, client_mod
    client_mod.reset_clients()
    assert client_mod._clients == {}


@pytest.mark.requisito("RF-005")
async def test_stream_access_denied_falls_back_to_converse_through_the_loop(env, priced, loop, bedrock_stream_provider):
    build, client_mod = bedrock_stream_provider
    env.tool_specs = [LIST_TOOL]
    stub = StubRuntimeClient(
        stream_error=client_error("AccessDeniedException", "no InvokeModelWithResponseStream"),
        converse_responses=[
            converse_message(
                [{"toolUse": {"toolUseId": "tu-1", "name": "list_career_record", "input": {"resource_key": "jobs"}}}],
                "tool_use", {"inputTokens": 100, "outputTokens": 20}),
            converse_message([{"text": "via converse"}], "end_turn", {"inputTokens": 150, "outputTokens": 30}),
        ],
    )
    provider = build(stub)
    priced(provider)
    executor = Recorder()

    events = await run(loop, provider, executor)

    # Cada ida y vuelta intenta ConverseStream y cae a Converse (fallback heredado de BedrockProvider.converse).
    assert [c[0] for c in stub.calls] == ["converse_stream", "converse", "converse_stream", "converse"]
    assert events[-1] == {"type": "done", "reply": "via converse", "affected_resources": []}
    assert [c["name"] for c in executor.calls] == ["list_career_record"]
    assert executor.calls[0]["input"] == {"resource_key": "jobs"}
    assert "runtime" in client_mod._clients  # el cliente salió del dict de módulo
    # El uso del turno es la suma de las dos rondas, leída del formato crudo de Bedrock.
    assert (env.turn_logs[0]["input_tokens"], env.turn_logs[0]["output_tokens"]) == (250, 50)


@pytest.mark.requisito("RF-005")
async def test_d26_two_streamed_tool_uses_in_one_message_stay_separate_through_the_loop(
    env, priced, loop, bedrock_stream_provider
):
    build, client_mod = bedrock_stream_provider
    env.tool_specs = [GET_TOOL]
    # Forma real del modelo de servicio de botocore: `contentBlockIndex` DENTRO de contentBlockStart/Delta/Stop.
    events_round_1 = [
        {"messageStart": {"role": "assistant"}},
        {"contentBlockStart": {"start": {"toolUse": {"toolUseId": "tu-a", "name": "get_career_record"}},
                               "contentBlockIndex": 0}},
        {"contentBlockDelta": {"delta": {"toolUse": {"input": '{"resource_key": "jobs", '}}, "contentBlockIndex": 0}},
        {"contentBlockDelta": {"delta": {"toolUse": {"input": '"record_id": "j1"}'}}, "contentBlockIndex": 0}},
        {"contentBlockStop": {"contentBlockIndex": 0}},
        {"contentBlockStart": {"start": {"toolUse": {"toolUseId": "tu-b", "name": "get_career_record"}},
                               "contentBlockIndex": 1}},
        {"contentBlockDelta": {"delta": {"toolUse": {"input": '{"resource_key": "jobs", "record_id": "j2"}'}},
                               "contentBlockIndex": 1}},
        {"contentBlockStop": {"contentBlockIndex": 1}},
        {"messageStop": {"stopReason": "tool_use"}},
        {"metadata": {"usage": {"inputTokens": 60, "outputTokens": 12}}},
    ]
    events_round_2 = [
        {"contentBlockDelta": {"delta": {"text": "Leí j1 y j2"}, "contentBlockIndex": 0}},
        {"messageStop": {"stopReason": "end_turn"}},
        {"metadata": {"usage": {"inputTokens": 90, "outputTokens": 8}}},
    ]
    stub = StubRuntimeClient(stream_events=[events_round_1, events_round_2])
    provider = build(stub)
    priced(provider)
    key = lambda rid: json.dumps(["get_career_record", {"resource_key": "jobs", "record_id": rid}], sort_keys=True)
    executor = Recorder(results={key("j1"): {"id": "j1", "title": "Uno"}, key("j2"): {"id": "j2", "title": "Dos"}})

    events = await run(loop, provider, executor)

    assert events[-1] == {"type": "done", "reply": "Leí j1 y j2", "affected_resources": []}
    # Dos tool calls distintas, en orden, sin mezclar ids ni argumentos.
    assert [(c["name"], c["input"]) for c in executor.calls] == [
        ("get_career_record", {"resource_key": "jobs", "record_id": "j1"}),
        ("get_career_record", {"resource_key": "jobs", "record_id": "j2"}),
    ]
    round2 = stub.calls[1][1]["messages"]
    assert round2[-2] == {"role": "assistant", "content": [
        {"toolUse": {"toolUseId": "tu-a", "name": "get_career_record",
                     "input": {"resource_key": "jobs", "record_id": "j1"}}},
        {"toolUse": {"toolUseId": "tu-b", "name": "get_career_record",
                     "input": {"resource_key": "jobs", "record_id": "j2"}}},
    ]}
    results = [b["toolResult"] for b in round2[-1]["content"]]
    assert [(r["toolUseId"], json.loads(r["content"][0]["text"])["id"]) for r in results] == [("tu-a", "j1"), ("tu-b", "j2")]
    assert [c[0] for c in stub.calls] == ["converse_stream", "converse_stream"]  # sin fallback: el stream funcionó


# =============================================================================================
# Ampliación (rechazo del revisor): paridad con TODO el comportamiento del bucle de la API
# =============================================================================================

def _key(name, tool_input):
    return json.dumps([name, tool_input], sort_keys=True)


def _statuses(events):
    return [e["message"] for e in events if e["type"] == "status"]


STATUS_MAX_TOKENS = "La respuesta se cortó por límite de tokens; reintentando en tandas más pequeñas..."
STATUS_PERSIST = "Persistiendo el contenido en la base de datos..."
STATUS_PROGRESS = "Continuando la tarea..."


# ---- max_tokens desde la configuración -------------------------------------------------------

@pytest.mark.requisito("RF-005")
async def test_max_tokens_is_read_from_settings_each_turn(env, priced, loop, monkeypatch):
    import config

    monkeypatch.setattr(config.settings, "BEDROCK_MAX_OUTPUT_TOKENS", 1234)
    provider = FakeProvider([text_reply()])
    priced(provider)
    await run(loop, provider)
    assert provider.requests[0].max_tokens == 1234


# ---- Nudges: funciones puras (api:166-256) ---------------------------------------------------

@pytest.mark.requisito("RF-005")
def test_should_retry_max_tokens_has_a_budget_of_two(loop):
    assert loop.should_retry_max_tokens("max_tokens", 0) is True
    assert loop.should_retry_max_tokens("max_tokens", 1) is True
    assert loop.should_retry_max_tokens("max_tokens", 2) is False
    assert loop.should_retry_max_tokens("max_tokens", 5, max_retries=6) is True
    assert loop.should_retry_max_tokens("end_turn", 0) is False
    assert loop.should_retry_max_tokens("tool_use", 0) is False
    assert loop.should_retry_max_tokens(None, 0) is False


@pytest.mark.requisito("RF-005")
@pytest.mark.parametrize("user_message", [
    "guarda esto", "Por favor GUARDAR el resumen", "genera el documento", "actualiza la metodología",
    "crea un registro", "escribe la guía", "documenta el proceso",           # intención de escritura
    "procede", "adelante", "hazlo", "aplícalo", "implementalo", "continúa",  # luz verde
])
def test_should_nudge_persist_positive_user_intent(loop, user_message):
    assert loop.should_nudge_persist("agent_methodologies", user_message, [], False, "Listo.") is True


@pytest.mark.requisito("RF-005")
@pytest.mark.parametrize("user_message", [
    "cuéntame qué es esto", "¿qué metodologías hay?", "gracias", "", None, "guardaespaldas", "procedente",
])
def test_should_nudge_persist_negative_user_messages(loop, user_message):
    assert loop.should_nudge_persist("agent_methodologies", user_message, [], False, "Claro.") is False


@pytest.mark.requisito("RF-005")
@pytest.mark.parametrize("assistant_text", [
    "Ahora actualizo opm-57 con el contenido.",
    "Voy a guardar los cambios.",
    "Procedo a modificar el registro.",
    "Actualizando los registros pendientes.",
    "actualizo OPM-57",
])
def test_should_nudge_persist_positive_assistant_write_claim(loop, assistant_text):
    # El mensaje del usuario es neutro: sólo la afirmación del asistente dispara el empujón.
    assert loop.should_nudge_persist("agent_methodologies", "revisa esto", [], False, assistant_text) is True


@pytest.mark.requisito("RF-005")
def test_should_nudge_persist_assistant_claim_only_counts_in_first_400_chars(loop):
    late = ("x" * 401) + " Voy a guardar los cambios."
    assert loop.should_nudge_persist("agent_methodologies", "revisa esto", [], False, late) is False
    assert loop.should_nudge_persist("agent_methodologies", "revisa esto", [], False, "Todo en orden.") is False


@pytest.mark.requisito("RF-005")
def test_should_nudge_persist_guards(loop):
    args = ("guarda esto", [], False, "Listo.")
    assert loop.should_nudge_persist("agent_methodologies", *args) is True
    assert loop.should_nudge_persist("agent_methodologies", "guarda esto", ["jobs"], False, "Listo.") is False  # ya escribió
    assert loop.should_nudge_persist("agent_methodologies", "guarda esto", [], True, "Listo.") is False        # ya se empujó
    assert loop.should_nudge_persist("agent_orchestrator", *args) is False   # L1: no es un L2 con write
    assert loop.should_nudge_persist("agent_pdf_render", *args) is False     # L3
    assert loop.should_nudge_persist("agent_web_search", *args) is False     # L3 sin write
    assert loop.should_nudge_persist("agent_networking", *args) is True      # cualquier L2 con write_enabled
    # compat histórica: mismo criterio
    assert loop.should_nudge_pdf_persist("agent_pdf_design", "guarda esto", [], False, "Listo.") is True
    assert loop.should_nudge_pdf_persist("agent_orchestrator", "guarda esto", [], False, "Listo.") is False


@pytest.mark.requisito("RF-005")
def test_persist_nudge_text_per_profile(loop):
    assert loop.persist_nudge_text("agent_pdf_design") == PDF_PERSIST_NUDGE
    assert loop.persist_nudge_text("agent_methodologies") == METHODOLOGIES_PERSIST_NUDGE
    assert loop.persist_nudge_text("agent_networking") == GENERIC_PERSIST_NUDGE
    assert loop.persist_nudge_text("agent_orchestrator") == GENERIC_PERSIST_NUDGE


@pytest.mark.requisito("RF-005")
@pytest.mark.parametrize("text", [
    "Voy a revisar los registros restantes.",
    "Ahora voy a consultar el siguiente.",
    "Procedo a leer el resto.",
    "A continuación reviso los demás.",
    "Continúo con la revisión del listado.",
    "Estos son los pasos:",
])
def test_should_nudge_progress_positive(loop, text):
    assert loop.should_nudge_progress(2, "revisa los registros", text, 0) is True


@pytest.mark.requisito("RF-005")
def test_should_nudge_progress_negative_cases(loop):
    stall = "Voy a revisar los registros restantes."
    assert loop.should_nudge_progress(1, "revisa", stall, 0) is False                     # sólo L2
    assert loop.should_nudge_progress(3, "revisa", stall, 0) is False
    assert loop.should_nudge_progress(2, "revisa", stall, 2) is False                     # cupo agotado
    assert loop.should_nudge_progress(2, "revisa", stall, 1) is True
    assert loop.should_nudge_progress(2, "revisa", stall, 0, max_nudges=0) is False
    for stop in ("detente", "cancela eso", "ya no sigas", "no continúes", "olvídalo", "déjalo así", "alto"):
        assert loop.should_nudge_progress(2, stop, stall, 0) is False                    # el usuario pidió parar
    assert loop.should_nudge_progress(2, None, stall, 0) is True
    assert loop.should_nudge_progress(2, "revisa", "", 0) is False
    assert loop.should_nudge_progress(2, "revisa", "   ", 0) is False
    assert loop.should_nudge_progress(2, "revisa", None, 0) is False
    assert loop.should_nudge_progress(2, "revisa", "No voy a revisar más registros.", 0) is False  # negado
    assert loop.should_nudge_progress(2, "revisa", "Ya está todo revisado.", 0) is False
    long_colon = ("a" * 700) + " pasos:"
    assert loop.should_nudge_progress(2, "revisa", long_colon, 0) is False               # ":" sólo si es corto (<600)
    old_claim = "Voy a revisar los registros. " + ("y " * 200) + "Terminé."
    assert loop.should_nudge_progress(2, "revisa", old_claim, 0) is False                # sólo cuenta la cola de 300 chars


# ---- Nudges dentro del bucle -----------------------------------------------------------------

@pytest.mark.requisito("RF-005")
async def test_loop_retries_after_max_tokens_cut_with_exact_nudge_and_forces_tool(env, priced, loop):
    env.settings["max_round_trips"] = 10
    env.tool_specs = [LIST_TOOL]
    provider = FakeProvider([
        tool_reply(ToolCall(id="tu-1", name="list_career_record", input={"resource_key": "jobs"})),
        text_reply("parcial", stop="max_tokens"),
        text_reply("ya", stop="end_turn"),
    ])
    priced(provider)

    events = await run(loop, provider)

    assert STATUS_MAX_TOKENS in _statuses(events)
    assert [r.force_tool_use for r in provider.requests] == [True, False, True]  # la ronda tras el corte fuerza tool
    assert provider.requests[2].messages[-2:] == [
        {"role": "assistant", "content": [{"text": "parcial"}]},
        {"role": "user", "content": [{"text": MAX_TOKENS_TRUNCATION_NUDGE}]},
    ]
    assert events[-1] == {"type": "done", "reply": "ya", "affected_resources": []}


@pytest.mark.requisito("RF-005")
async def test_max_tokens_retry_uses_placeholder_when_no_text_and_stops_after_two(env, priced, loop):
    env.settings["max_round_trips"] = 10
    env.tool_specs = [LIST_TOOL]
    cut = lambda: text_reply("", stop="max_tokens")
    provider = FakeProvider([cut(), cut(), cut()])
    priced(provider)

    events = await run(loop, provider)

    assert len(provider.requests) == 3
    assert _statuses(events).count(STATUS_MAX_TOKENS) == 2  # tope de 2 reintentos
    assert provider.requests[1].messages[-2:] == [
        {"role": "assistant", "content": [{"text": "(sin texto)"}]},
        {"role": "user", "content": [{"text": MAX_TOKENS_TRUNCATION_NUDGE}]},
    ]
    assert events[-1] == {"type": "done", "reply": "(sin texto)", "affected_resources": []}


@pytest.mark.requisito("RF-005")
async def test_max_tokens_stop_with_a_complete_tool_call_executes_it_without_nudge(env, priced, loop):
    env.tool_specs = [LIST_TOOL]
    executor = Recorder()
    provider = FakeProvider([
        ModelResponse(text="", stop_reason="max_tokens", usage=Usage(1, 1),
                      tool_calls=[ToolCall(id="tu-1", name="list_career_record", input={"resource_key": "jobs"})]),
        text_reply("fin"),
    ])
    priced(provider)

    events = await run(loop, provider, executor)

    assert [c["name"] for c in executor.calls] == ["list_career_record"]
    assert STATUS_MAX_TOKENS not in _statuses(events)


@pytest.mark.requisito("RF-005")
async def test_loop_persist_nudge_fires_once_with_profile_text_and_forces_tool(env, priced, loop):
    env.tool_specs = [UPDATE_TOOL]
    provider = FakeProvider([text_reply("Listo, queda así."), text_reply("Sigue sin guardar.")])
    priced(provider)

    events = await run(loop, provider, message="guarda esto", surface="contextual",
                       req_kw=dict(agent_profile_id="agent_methodologies"))

    assert STATUS_PERSIST in _statuses(events) and _statuses(events).count(STATUS_PERSIST) == 1
    assert [r.force_tool_use for r in provider.requests] == [True, True]
    assert provider.requests[1].messages[-2:] == [
        {"role": "assistant", "content": [{"text": "Listo, queda así."}]},
        {"role": "user", "content": [{"text": METHODOLOGIES_PERSIST_NUDGE}]},
    ]
    # Una sola vez por turno: la segunda respuesta sin escritura cierra el turno.
    assert len(provider.requests) == 2
    assert events[-1] == {"type": "done", "reply": "Sigue sin guardar.", "affected_resources": []}


@pytest.mark.requisito("RF-005")
async def test_loop_no_persist_nudge_after_a_successful_write(env, priced, loop):
    env.tool_specs = [UPDATE_TOOL]
    write = ToolCall(id="tu-1", name="update_career_record",
                     input={"resource_key": "operational-methodologies", "record_id": "opm-57", "fields": {}})
    provider = FakeProvider([tool_reply(write), text_reply("Guardado.")])
    priced(provider)

    events = await run(loop, provider, message="guarda esto", surface="contextual",
                       req_kw=dict(agent_profile_id="agent_methodologies"))

    assert STATUS_PERSIST not in _statuses(events)
    assert len(provider.requests) == 2
    assert events[-1] == {"type": "done", "reply": "Guardado.", "affected_resources": ["operational-methodologies"]}


@pytest.mark.requisito("RF-005")
async def test_loop_persist_nudge_for_pdf_profile_uses_pdf_text(env, priced, loop):
    env.tool_specs = [UPDATE_TOOL]
    provider = FakeProvider([text_reply("Hecho."), text_reply("Hecho otra vez.")])
    priced(provider)
    await run(loop, provider, message="genera el estilo", surface="contextual",
              req_kw=dict(agent_profile_id="agent_pdf_design"))
    assert provider.requests[1].messages[-1] == {"role": "user", "content": [{"text": PDF_PERSIST_NUDGE}]}


@pytest.mark.requisito("RF-005")
async def test_loop_progress_nudge_up_to_twice_with_exact_text_and_forced_tool(env, priced, loop):
    env.settings["max_round_trips"] = 10
    env.tool_specs = [LIST_TOOL]
    stall = "Voy a revisar el siguiente."
    provider = FakeProvider([
        tool_reply(ToolCall(id="tu-1", name="list_career_record", input={"resource_key": "contacts"})),
        text_reply(stall), text_reply(stall), text_reply(stall),
    ])
    priced(provider)

    events = await run(loop, provider, message="revisa mis contactos", surface="contextual",
                       req_kw=dict(agent_profile_id="agent_networking"))

    assert _statuses(events).count(STATUS_PROGRESS) == 2  # max_nudges=2
    assert [r.force_tool_use for r in provider.requests] == [True, False, True, True]
    assert provider.requests[2].messages[-2:] == [
        {"role": "assistant", "content": [{"text": stall}]},
        {"role": "user", "content": [{"text": PROGRESS_STALL_NUDGE}]},
    ]
    assert len(provider.requests) == 4
    assert events[-1] == {"type": "done", "reply": stall, "affected_resources": []}


@pytest.mark.requisito("RF-005")
async def test_loop_no_progress_nudge_for_l1_or_when_user_asked_to_stop(env, priced, loop):
    env.tool_specs = [LIST_TOOL]
    stall = "Voy a revisar el siguiente."
    p1 = FakeProvider([text_reply(stall)])
    priced(p1)
    ev1 = await run(loop, p1, message="revisa", surface="general")  # L1
    assert STATUS_PROGRESS not in _statuses(ev1) and len(p1.requests) == 1

    p2 = FakeProvider([text_reply(stall)])
    priced(p2)
    ev2 = await run(loop, p2, message="detente ya", surface="contextual",
                    req_kw=dict(agent_profile_id="agent_networking"))
    assert STATUS_PROGRESS not in _statuses(ev2) and len(p2.requests) == 1


# ---- Adjuntos (api:510) ----------------------------------------------------------------------

@pytest.mark.requisito("RF-005")
async def test_attachments_are_turned_into_user_content_blocks(env, priced, loop):
    provider = FakeProvider([text_reply("vi la foto")])
    priced(provider)
    attachments = [{"file_id": "f1"}]

    events = await run(loop, provider, message="mira", req_kw=dict(attachments=attachments))

    assert env.content_calls == [("u1", "mira", attachments)]
    assert provider.requests[0].messages == [{"role": "user", "content": [
        {"text": "mira\n\n[Adjunto: foto.png] (imagen incluida)"},
        {"image": {"format": "png", "source": {"bytes": b"PNG"}}},
    ]}]
    # El historial persiste el texto original, no los bloques.
    assert env.appended[0] == ("conv-1", "user", "mira")
    assert events[-1]["reply"] == "vi la foto"


@pytest.mark.requisito("RF-005")
async def test_attachment_error_propagates_before_calling_the_model(env, priced, loop, monkeypatch):
    async def boom(db, user_id, message, attachments):
        raise ProviderError("Adjunto no encontrado: file_id=f9")

    monkeypatch.setattr(loop, "build_user_content_blocks", boom)
    provider = FakeProvider([text_reply()])
    priced(provider)

    with pytest.raises(ProviderError, match="Adjunto no encontrado: file_id=f9"):
        await run(loop, provider, req_kw=dict(attachments=[{"file_id": "f9"}]))

    assert provider.requests == [] and env.created == []


# ---- affected_resources y seen_reads (api:759-779) --------------------------------------------

@pytest.mark.requisito("RF-005")
async def test_affected_resources_collect_invalidation_keys_without_duplicates(env, priced, loop):
    env.tool_specs = [UPDATE_TOOL, GET_TOOL]
    upd = lambda i, rk: ToolCall(id=f"tu-{i}", name="update_career_record", input={"resource_key": rk, "record_id": "x"})
    failing = ToolCall(id="tu-4", name="update_career_record", input={"resource_key": "contacts", "record_id": "x"})
    executor = Recorder(results={_key("update_career_record", failing.input): {"error": "422"}})
    provider = FakeProvider([tool_reply(upd(1, "jobs"), upd(2, "skills"), upd(3, "jobs"), failing), text_reply("ok")])
    priced(provider)

    events = await run(loop, provider, executor)

    assert events[-1] == {"type": "done", "reply": "ok", "affected_resources": ["jobs", "skills"]}


@pytest.mark.requisito("RF-005")
async def test_a_successful_write_clears_seen_reads_so_the_same_read_runs_again(env, priced, loop):
    env.tool_specs = [GET_TOOL, UPDATE_TOOL]
    get = lambda i: ToolCall(id=f"tu-g{i}", name="get_career_record", input={"resource_key": "jobs", "record_id": "j1"})
    upd = ToolCall(id="tu-u", name="update_career_record", input={"resource_key": "jobs", "record_id": "j1"})
    executor = Recorder()
    provider = FakeProvider([tool_reply(get(1)), tool_reply(upd), tool_reply(get(2)), text_reply("fin")])
    priced(provider)

    await run(loop, provider, executor)

    assert [c["name"] for c in executor.calls] == ["get_career_record", "update_career_record", "get_career_record"]


@pytest.mark.requisito("RF-005")
async def test_a_failed_write_does_not_clear_seen_reads(env, priced, loop):
    env.tool_specs = [GET_TOOL, UPDATE_TOOL]
    get = lambda i: ToolCall(id=f"tu-g{i}", name="get_career_record", input={"resource_key": "jobs", "record_id": "j1"})
    upd = ToolCall(id="tu-u", name="update_career_record", input={"resource_key": "jobs", "record_id": "j1"})
    executor = Recorder(results={_key("update_career_record", upd.input): {"error": "422"}})
    provider = FakeProvider([tool_reply(get(1)), tool_reply(upd), tool_reply(get(2)), text_reply("fin")])
    priced(provider)

    events = await run(loop, provider, executor)

    assert [c["name"] for c in executor.calls] == ["get_career_record", "update_career_record"]
    assert events[-1]["affected_resources"] == []


# ---- Nivel 3 (api:474-479) --------------------------------------------------------------------

@pytest.mark.requisito("RF-005")
async def test_level_3_agents_have_no_user_chat_when_recording_history(env, priced, loop):
    provider = FakeProvider([text_reply()])
    priced(provider)

    events = await run(loop, provider, surface="contextual", req_kw=dict(agent_profile_id="agent_pdf_render"))

    assert events == [{"type": "error",
                       "message": "Los agentes de nivel 3 no tienen chat con el usuario. Delega desde L1 o L2."}]
    assert provider.requests == [] and env.context_args == [] and env.created == []


@pytest.mark.requisito("RF-005")
async def test_level_3_agent_runs_as_a_sub_turn_without_history(env, priced, loop):
    provider = FakeProvider([text_reply("resultado L3")])
    priced(provider)

    events = await run(loop, provider, surface="contextual", record_history=False,
                       req_kw=dict(agent_profile_id="agent_pdf_render"))

    assert events[-1] == {"type": "done", "reply": "resultado L3", "affected_resources": []}
    assert provider.requests[0].model_id == NOVA  # default del perfil L3


# ---- Elección de modelo (api:281-325) ---------------------------------------------------------

@pytest.mark.requisito("RF-005")
async def test_weak_model_requested_in_contextual_surface_is_ignored(env, priced, loop):
    provider = FakeProvider([text_reply(), text_reply()])
    priced(provider)
    ctx = dict(agent_profile_id="agent_orchestrator")
    await run(loop, provider, surface="contextual", req_kw=dict(model_id=NOVA, **ctx))     # débil: se ignora
    await run(loop, provider, surface="contextual", req_kw=dict(model_id=SONNET, **ctx))   # no débil: se respeta
    assert [r.model_id for r in provider.requests] == [HAIKU, SONNET]


@pytest.mark.requisito("RF-005")
async def test_general_surface_ignores_the_requested_model(env, priced, loop):
    provider = FakeProvider([text_reply()])
    priced(provider)
    await run(loop, provider, surface="general", req_kw=dict(model_id=SONNET))
    assert provider.requests[0].model_id == HAIKU  # default del orquestador, no lo pedido


@pytest.mark.requisito("RF-005")
async def test_general_surface_falls_back_to_runtime_orchestrator_model(env, priced, loop):
    # El default del orquestador (Haiku) no está en el catálogo del provider -> modelo del runtime.
    provider = FakeProvider([text_reply()], models=[SONNET, NOVA])
    priced(provider)
    await run(loop, provider, surface="general")
    assert provider.requests[0].model_id == RUNTIME_MODEL


@pytest.mark.requisito("RF-005")
@pytest.mark.parametrize("requested", [None, "otro.modelo-no-listado", NOVA])
async def test_contextual_last_resort_is_the_recommended_model_for_the_page(env, priced, loop, requested):
    # Ni lo pedido (ausente, desconocido o débil) ni el default del perfil (Haiku, no listado) sirven.
    provider = FakeProvider([text_reply()], models=[SONNET, NOVA])
    priced(provider)
    page = {"route": "/vacancies", "resource_key": "vacancies"}

    await run(loop, provider, surface="contextual",
              req_kw=dict(page_context=page, agent_profile_id="agent_orchestrator", model_id=requested))

    assert provider.requests[0].model_id == SONNET  # lo que devuelve resolve_recommended_model
    assert env.recommended_calls == [page]


# ---- Textos de estado por tool (api:32-64) ----------------------------------------------------

def _api_tool_status():
    import ast
    from pathlib import Path

    src = Path(__file__).resolve().parents[4] / "cjhirashi-career-api/src/services/bedrock/agent_loop.py"
    if not src.exists():
        pytest.skip("API de referencia no disponible")
    for node in ast.parse(src.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "_TOOL_STATUS":
            return ast.literal_eval(node.value)
    raise AssertionError("_TOOL_STATUS no encontrado en la API")


TOOL_STATUS = {
    "describe_resource_schema": "Revisando la estructura de la tabla...",
    "search_knowledge_base": "Consultando la base de conocimiento...",  # entrada muerta (T-086): paridad textual
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


@pytest.mark.requisito("RF-005")
def test_tool_status_table_is_the_one_of_the_api():
    # `search_knowledge_base` se mantiene por paridad textual con la API, pero es una entrada MUERTA:
    # la tool no existe en el harness (ver T-086).
    assert TOOL_STATUS == _api_tool_status()


@pytest.mark.requisito("RF-005")
@pytest.mark.parametrize("tool_name,text", sorted(TOOL_STATUS.items()))
async def test_status_event_text_per_tool(env, priced, loop, tool_name, text):
    provider = FakeProvider([tool_reply(ToolCall(id="t1", name=tool_name, input={})), text_reply()])
    priced(provider)
    env.tool_specs = [ToolSpec(name=tool_name, description="x", input_schema={"type": "object"})]

    events = await run(loop, provider, Recorder())

    assert _statuses(events)[:2] == ["Pensando...", text]


@pytest.mark.requisito("RF-005")
async def test_status_event_default_text_for_unknown_tool(env, priced, loop):
    provider = FakeProvider([tool_reply(ToolCall(id="t1", name="herramienta_rara", input={})), text_reply()])
    priced(provider)
    env.tool_specs = [ToolSpec(name="herramienta_rara", description="x", input_schema={"type": "object"})]

    events = await run(loop, provider, Recorder())

    assert _statuses(events)[:2] == ["Pensando...", "Usando herramienta_rara..."]


# ---- Delegación: sólo el enganche (T-090/T-091 completan la implementación) ---------------------

def delegate_call(i, target="agent_networking", task="haz esto", context="ctx"):
    return ToolCall(id=f"tu-d{i}", name="delegate_to_specialist",
                    input={"agent_profile_id": target, "task": task, "context": context})


@pytest.mark.requisito("RF-005")
async def test_delegation_hook_emits_events_calls_sub_turn_and_feeds_summary_back(env, priced, loop):
    env.delegate_ids = ["agent_networking"]
    env.sub_result = {"summary": "contactos revisados", "affected_resources": ["contacts"]}
    executor = Recorder()
    task = "x" * 130
    provider = FakeProvider([tool_reply(delegate_call(1, task=task)), text_reply("listo")])
    priced(provider)

    events = await run(loop, provider, executor)

    assert events == [
        {"type": "status", "message": "Pensando..."},
        {"type": "status", "message": "Consultando especialista..."},
        {"type": "delegation_start", "agent_profile_id": "agent_networking", "label": "Networking", "level": 2,
         "task_preview": "x" * 120},
        {"type": "delegation_end", "agent_profile_id": "agent_networking", "success": True,
         "summary_preview": "contactos revisados"},
        {"type": "done", "reply": "listo", "affected_resources": ["contacts"]},
    ]
    assert env.sub_turns == [dict(user_id="u1", session_id="s1", profile_id="agent_networking", task=task,
                                  context="ctx", delegation_depth=0)]
    assert executor.calls == []  # la delegación no pasa por el ejecutor de tools
    result = provider.requests[1].messages[-1]["content"][0]["toolResult"]
    assert result == {"toolUseId": "tu-d1", "status": "success",
                      "content": [{"text": json.dumps(env.sub_result, ensure_ascii=False)}]}


@pytest.mark.requisito("RF-005")
async def test_delegation_denials_are_returned_to_the_model_as_error_results(env, priced, loop):
    env.delegate_ids = ["agent_networking"]
    cases = [
        # (llamada, kwargs de run, error esperado)
        (delegate_call(1), dict(delegation_depth=2), "max delegation depth exceeded"),
        (delegate_call(2, target="agent_support"), {}, "delegation not allowed: agent_support is not in this agent's configured targets"),
        (delegate_call(3, target="agent_nope"), {}, "unknown agent profile: agent_nope"),
    ]
    for call, kw, expected in cases:
        provider = FakeProvider([tool_reply(call), text_reply("ok")])
        priced(provider)
        events = await run(loop, provider, **kw)
        result = provider.requests[1].messages[-1]["content"][0]["toolResult"]
        assert result["status"] == "error"
        assert json.loads(result["content"][0]["text"]) == {"error": expected}
        assert not any(e["type"].startswith("delegation_") for e in events)
    assert env.sub_turns == []


@pytest.mark.requisito("RF-005")
async def test_profile_that_cannot_delegate_is_denied(env, priced, loop):
    provider = FakeProvider([tool_reply(delegate_call(1)), text_reply("ok")])
    priced(provider)
    await run(loop, provider, surface="contextual", record_history=False,
              req_kw=dict(agent_profile_id="agent_pdf_render"))
    result = provider.requests[1].messages[-1]["content"][0]["toolResult"]
    assert result["status"] == "error"
    assert json.loads(result["content"][0]["text"]) == {"error": "this profile cannot delegate"}
    assert env.sub_turns == []


@pytest.mark.requisito("RF-005")
async def test_delegations_per_turn_are_capped_by_settings(env, priced, loop):
    import config

    # T-085 añade `BEDROCK_MAX_DELEGATIONS_PER_TURN: int = 3` a `config.Settings` (hoy sólo existe en la API).
    assert config.settings.BEDROCK_MAX_DELEGATIONS_PER_TURN == 3
    env.delegate_ids = ["agent_networking"]
    calls = [delegate_call(i, task=f"t{i}") for i in range(1, 5)]
    provider = FakeProvider([tool_reply(*calls), text_reply("ok")])
    priced(provider)

    await run(loop, provider)

    assert [s["task"] for s in env.sub_turns] == ["t1", "t2", "t3"]  # BEDROCK_MAX_DELEGATIONS_PER_TURN = 3
    results = [b["toolResult"] for b in provider.requests[1].messages[-1]["content"]]
    assert [r["status"] for r in results] == ["success", "success", "success", "error"]
    assert json.loads(results[3]["content"][0]["text"]) == {"error": "max delegations per turn exceeded"}
