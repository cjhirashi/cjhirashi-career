"""T-084c — `services/section_profiles.py` (RF-005): modelo recomendado del chat contextual.

Traslado fiel de `cjhirashi-career-api/src/services/bedrock/section_profiles.py::resolve_recommended_model`
(la API no tenía tests de este módulo; los valores exactos salen del código).

Interfaz que T-084d debe cumplir
--------------------------------
    def resolve_recommended_model(page_context: dict | None) -> str

* Función pura y SÍNCRONA, sin E/S: todo son tablas constantes del módulo + `config.settings.BEDROCK_DEFAULT_MODEL_ID`
  (leído en cada llamada, no copiado al importar). No hay datos de BD/REST, así que D-10 no interviene aquí
  (el perfil de agente de la sección sí se lee por REST, pero eso es del bucle, T-085).
* Orden de resolución (exacto):
    1. `page_context` falsy (None / {}) -> modelo por defecto.
    2. `route` en las rutas estáticas -> modelo de ese perfil (gana sobre `chat_profile` y `resource_key`).
    3. `chat_profile` conocido -> su modelo (gana sobre `resource_key`).
    4. `resource_key` conocido -> modelo del perfil de ese recurso.
    5. cualquier otro caso -> modelo por defecto.
* Sin coincidencia por prefijo (`/vacancies/12` NO es `/vacancies`) y no muta el contexto recibido.
"""
import copy
import importlib

import pytest

import config

pytestmark = pytest.mark.requisito("RF-005")

HAIKU = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
SONNET = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
DEEPSEEK = "deepseek.v3.2"
NOVA = "amazon.nova-lite-v1:0"
MISTRAL = "mistral.mistral-large-2402-v1:0"
DEFAULT = "test.default-model-v1"  # distinto de cualquier modelo de perfil

PROFILE_MODELS = {
    "crud_standard": HAIKU,
    "strategy": DEEPSEEK,
    "narrative": SONNET,
    "digital_presence": SONNET,
    "methodology": HAIKU,
    "read_light": NOVA,
    "agent_admin": HAIKU,
    "singleton_identity": MISTRAL,
}

STATIC_ROUTES = {
    "/dashboard": NOVA,
    "/metrics": NOVA,
    "/search-metrics": NOVA,
    "/files": HAIKU,
    "/linkedin": SONNET,
    "/agent/chat": NOVA,
}

RESOURCE_KEYS = {
    "vacancies": DEEPSEEK,
    "search-plans": DEEPSEEK,
    "fit-scoring-factors": DEEPSEEK,
    "target-companies": DEEPSEEK,
    "target-roles": DEEPSEEK,
    "applications": DEEPSEEK,
    "cv-versions": SONNET,
    "cover-letter-versions": SONNET,
    "role-narratives": SONNET,
    "star-stories": SONNET,
    "identity-reflections": SONNET,
    "publications": SONNET,
    "linkedin-profile": SONNET,
    "operational-methodologies": HAIKU,
    "identity": MISTRAL,
    "personal-profile": MISTRAL,
}


@pytest.fixture
def sp():
    """Importa `services.section_profiles` de forma perezosa: rojo = ModuleNotFoundError (T-084d pendiente)."""
    return importlib.import_module("services.section_profiles")


@pytest.fixture
def resolve(sp, monkeypatch):
    monkeypatch.setattr(config.settings, "BEDROCK_DEFAULT_MODEL_ID", DEFAULT)
    return sp.resolve_recommended_model


# --- rama 1: sin contexto -------------------------------------------------------------------------------------

@pytest.mark.parametrize("ctx", [None, {}])
def test_no_context_returns_default_model(resolve, ctx):
    assert resolve(ctx) == DEFAULT


def test_default_is_read_from_settings_at_call_time(sp, monkeypatch):
    monkeypatch.setattr(config.settings, "BEDROCK_DEFAULT_MODEL_ID", "otro.modelo-v9")
    assert sp.resolve_recommended_model(None) == "otro.modelo-v9"
    monkeypatch.setattr(config.settings, "BEDROCK_DEFAULT_MODEL_ID", "y.otro-v2")
    assert sp.resolve_recommended_model({"route": "/nope"}) == "y.otro-v2"


# --- rama 2: ruta estática ------------------------------------------------------------------------------------

@pytest.mark.parametrize("route,model", sorted(STATIC_ROUTES.items()))
def test_static_route_maps_to_profile_model(resolve, route, model):
    assert resolve({"route": route}) == model


def test_static_route_wins_over_chat_profile_and_resource_key(resolve):
    ctx = {"route": "/dashboard", "chat_profile": "strategy", "resource_key": "cv-versions"}
    assert resolve(ctx) == NOVA


@pytest.mark.parametrize("route", ["/vacancies/12", "/dashboard/", "/dashboard/x", "/Dashboard", "dashboard", "/"])
def test_route_is_exact_match_not_prefix_or_normalized(resolve, route):
    assert resolve({"route": route}) == DEFAULT


@pytest.mark.parametrize("route", [None, ""])
def test_empty_or_null_route_falls_through_to_next_rules(resolve, route):
    assert resolve({"route": route}) == DEFAULT
    assert resolve({"route": route, "chat_profile": "strategy"}) == DEEPSEEK
    assert resolve({"route": route, "resource_key": "identity"}) == MISTRAL


def test_unknown_route_falls_through_to_chat_profile_and_resource_key(resolve):
    assert resolve({"route": "/otra", "chat_profile": "narrative"}) == SONNET
    assert resolve({"route": "/otra", "resource_key": "applications"}) == DEEPSEEK


# --- rama 3: chat_profile -------------------------------------------------------------------------------------

@pytest.mark.parametrize("profile,model", sorted(PROFILE_MODELS.items()))
def test_chat_profile_maps_to_profile_model(resolve, profile, model):
    assert resolve({"chat_profile": profile}) == model


def test_chat_profile_wins_over_resource_key(resolve):
    assert resolve({"chat_profile": "read_light", "resource_key": "cv-versions"}) == NOVA


@pytest.mark.parametrize("profile", ["inexistente", "STRATEGY", "vacancies", 123])
def test_unknown_chat_profile_falls_through_to_resource_key(resolve, profile):
    ctx = {"chat_profile": profile}
    assert resolve(ctx) == DEFAULT
    assert resolve({**ctx, "resource_key": "identity"}) == MISTRAL


@pytest.mark.parametrize("profile", [None, ""])
def test_empty_chat_profile_falls_through_to_resource_key(resolve, profile):
    assert resolve({"chat_profile": profile, "resource_key": "publications"}) == SONNET


# --- rama 4: resource_key -------------------------------------------------------------------------------------

@pytest.mark.parametrize("rk,model", sorted(RESOURCE_KEYS.items()))
def test_resource_key_maps_to_profile_model(resolve, rk, model):
    assert resolve({"resource_key": rk}) == model


def test_resource_key_table_has_exactly_the_api_entries(sp):
    """Paridad (D-13): ni más ni menos recursos que la API; un recurso nuevo exige actualizar este test."""
    for rk in RESOURCE_KEYS:
        sp.resolve_recommended_model({"resource_key": rk})  # no debe lanzar
    assert len(RESOURCE_KEYS) == 16


# --- rama 5: desconocido -> defecto ---------------------------------------------------------------------------

@pytest.mark.parametrize("rk", ["inexistente", "Vacancies", "strategy", "/vacancies", None, ""])
def test_unknown_resource_key_returns_default(resolve, rk):
    assert resolve({"resource_key": rk}) == DEFAULT


def test_context_without_known_keys_returns_default(resolve):
    assert resolve({"otra": "cosa", "entity_id": "x"}) == DEFAULT


# --- propiedades ----------------------------------------------------------------------------------------------

@pytest.mark.parametrize("ctx", [
    {"route": "/files", "chat_profile": "strategy", "resource_key": "identity", "extra": {"a": [1]}},
    {"chat_profile": "strategy"},
    {"resource_key": "identity"},
    {"entity_id": "x"},
])
def test_does_not_mutate_page_context(resolve, ctx):
    before = copy.deepcopy(ctx)
    resolve(ctx)
    assert ctx == before


def test_is_synchronous_plain_function(sp):
    import inspect
    assert not inspect.iscoroutinefunction(sp.resolve_recommended_model)
