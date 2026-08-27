"""Costo estimado con tokens de prompt caching de Bedrock."""
from services.bedrock.usage_logger import (
    _cache_tokens,
    _estimate_cost,
    cache_read_savings_usd,
)

HAIKU = "us.anthropic.claude-haiku-4-5-20251001-v1:0"  # $1.00/M entrada, $5.00/M salida


def test_estimate_cost_without_cache_matches_plain_rates():
    cost = _estimate_cost(HAIKU, input_tokens=1_000_000, output_tokens=0)
    assert cost == 1.0


def test_cache_read_billed_at_ten_percent_of_input():
    cost = _estimate_cost(HAIKU, input_tokens=0, output_tokens=0, cache_read_tokens=1_000_000)
    assert round(cost, 6) == 0.10


def test_cache_write_billed_at_125_percent_of_input():
    cost = _estimate_cost(HAIKU, input_tokens=0, output_tokens=0, cache_write_tokens=1_000_000)
    assert round(cost, 6) == 1.25


def test_unknown_model_is_free():
    assert _estimate_cost("modelo-inexistente", 999, 999, 999, 999) == 0.0


def test_cache_tokens_helper_reads_converse_usage_keys():
    usage = {"inputTokens": 10, "cacheReadInputTokens": 7, "cacheWriteInputTokens": 3}
    assert _cache_tokens(usage) == (7, 3)
    assert _cache_tokens(None) == (0, 0)
    assert _cache_tokens({}) == (0, 0)


def test_cache_read_savings_is_ninety_percent_of_input_price():
    # 1M tokens leídos de caché: precio normal $1.00, con caché $0.10 → ahorro $0.90
    assert round(cache_read_savings_usd(HAIKU, 1_000_000), 6) == 0.90
    assert cache_read_savings_usd(HAIKU, 0) == 0.0
    assert cache_read_savings_usd("modelo-inexistente", 1_000_000) == 0.0
