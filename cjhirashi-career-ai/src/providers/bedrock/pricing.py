"""
Catálogo de modelos y tabla de precios de Bedrock (traslado de api config.BEDROCK_AVAILABLE_MODELS
y services/bedrock/usage_logger.py::_estimate_cost). Precios USD por millón de tokens.

Solo modelos que el harness usa hoy. El prompt caching (ADR-019) aplica a los que llevan
`supports_prompt_cache=True` (Claude 4.5).
"""
from typing import Dict, List

from providers.base import ModelInfo, Usage

# Ratios estándar de prompt caching (Anthropic / Bedrock), relativos al precio de entrada normal:
# lectura de caché 0.10x y escritura 1.25x. OJO: 1.25x asume TTL de 5 min, que es lo que emite
# converse.cache_point() ({"type": "default"}). Si algún día se usa {"ttl": "1h"}, la escritura
# pasa a 2.0x y hay que parametrizar este ratio.
CACHE_READ_RATIO = 0.10
CACHE_WRITE_RATIO = 1.25

MODEL_CATALOG: Dict[str, ModelInfo] = {
    m.model_id: m
    for m in (
        ModelInfo("amazon.nova-lite-v1:0", "Nova Lite", "economy", "foundation", 0.06, 0.24),
        ModelInfo("deepseek.v3.2", "DeepSeek V3.2", "economy", "foundation", 0.62, 1.85),
        ModelInfo(
            "us.anthropic.claude-haiku-4-5-20251001-v1:0", "Claude Haiku 4.5", "standard",
            "inference_profile", 1.00, 5.00, True,
        ),
        ModelInfo(
            "mistral.mistral-large-2402-v1:0", "Mistral Large", "standard", "foundation", 2.00, 6.00
        ),
        ModelInfo(
            "us.anthropic.claude-sonnet-4-5-20250929-v1:0", "Claude Sonnet 4.5", "premium",
            "inference_profile", 3.00, 15.00, True,
        ),
    )
}


def list_models() -> List[ModelInfo]:
    return list(MODEL_CATALOG.values())


def supports_prompt_cache(model_id: str) -> bool:
    info = MODEL_CATALOG.get(model_id)
    return bool(info and info.supports_prompt_cache)


def estimate_cost(model_id: str, usage: Usage) -> float:
    """Coste estimado en USD; 0 para un modelo fuera del catálogo."""
    info = MODEL_CATALOG.get(model_id)
    price_in = (info.price_input_per_million if info else 0) / 1_000_000
    price_out = (info.price_output_per_million if info else 0) / 1_000_000
    return (
        usage.input_tokens * price_in
        + usage.output_tokens * price_out
        + usage.cache_read_tokens * price_in * CACHE_READ_RATIO
        + usage.cache_write_tokens * price_in * CACHE_WRITE_RATIO
    )


def cache_read_savings_usd(model_id: str, cache_read_tokens: int) -> float:
    """Ahorro estimado por servir esos tokens desde caché (0.10x) en vez de a precio normal (1.0x)."""
    info = MODEL_CATALOG.get(model_id)
    price_in = (info.price_input_per_million if info else 0) / 1_000_000
    return cache_read_tokens * price_in * (1 - CACHE_READ_RATIO)
