"""
Mapeo ruta/recurso → modelo recomendado (chat contextual).

Mirror de admin/src/config/chatSectionProfiles.ts. Ver docs/BEDROCK-SYSTEM.md.
"""
from typing import Optional

from config import settings

_PROFILE_MODELS = {
    "crud_standard": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
    "strategy": "deepseek.v3.2",
    "narrative": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "digital_presence": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "methodology": "cohere.command-r-v1:0",
    "read_light": "amazon.nova-lite-v1:0",
    "agent_admin": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
    "singleton_identity": "mistral.mistral-large-2402-v1:0",
}

_RESOURCE_CHAT_PROFILE = {
    "vacancies": "strategy",
    "search-plans": "strategy",
    "fit-scoring-factors": "strategy",
    "target-companies": "strategy",
    "target-roles": "strategy",
    "applications": "strategy",
    "cv-versions": "narrative",
    "cover-letter-versions": "narrative",
    "role-narratives": "narrative",
    "star-stories": "narrative",
    "identity-reflections": "narrative",
    "publications": "digital_presence",
    "linkedin-profile": "digital_presence",
    "operational-methodologies": "methodology",
    "identity": "singleton_identity",
}

_STATIC_ROUTE_PROFILE = {
    "/dashboard": "read_light",
    "/metrics": "read_light",
    "/search-metrics": "read_light",
    "/files": "agent_admin",
    "/linkedin": "digital_presence",
    "/agent/chat": "read_light",
}


def resolve_recommended_model(page_context: Optional[dict]) -> str:
    """Modelo sugerido según sección; fallback a default global."""
    if not page_context:
        return settings.BEDROCK_DEFAULT_MODEL_ID
    route = page_context.get("route") or ""
    if route in _STATIC_ROUTE_PROFILE:
        return _PROFILE_MODELS[_STATIC_ROUTE_PROFILE[route]]
    chat_profile = page_context.get("chat_profile")
    if chat_profile and chat_profile in _PROFILE_MODELS:
        return _PROFILE_MODELS[chat_profile]
    rk = page_context.get("resource_key")
    if rk and rk in _RESOURCE_CHAT_PROFILE:
        return _PROFILE_MODELS[_RESOURCE_CHAT_PROFILE[rk]]
    return settings.BEDROCK_DEFAULT_MODEL_ID
