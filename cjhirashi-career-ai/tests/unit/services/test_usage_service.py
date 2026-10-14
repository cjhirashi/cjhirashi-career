"""RF-006: servicio de uso: coste estimado, registro best-effort, presupuesto y métricas (T-064)."""
import logging

import pytest

from providers.base import Usage

pytestmark = pytest.mark.requisito("RF-006")

HAIKU = "us.anthropic.claude-haiku-4-5-20251001-v1:0"


def _usage(**kw):
    return Usage(**{"input_tokens": 1_000_000, "output_tokens": 1_000_000, **kw})


async def test_record_turn_usage_calcula_coste_con_cache(pg_db):
    from models import BedrockUsageLog
    from services import usage_service

    await usage_service.record_turn_usage(
        "usr-1", "s1", HAIKU, _usage(cache_read_tokens=1_000_000, cache_write_tokens=1_000_000), session_factory=pg_db
    )
    async with pg_db() as s:
        row = await s.get(BedrockUsageLog, 1)
        # 1.00 (in) + 5.00 (out) + 0.10 (cache read) + 1.25 (cache write)
        assert float(row.estimated_cost_usd) == pytest.approx(7.35)
        assert (row.cache_read_tokens, row.cache_write_tokens) == (1_000_000, 1_000_000)


async def test_record_round_log_con_coste_fijo_y_sin_modelo(pg_db):
    from models import BedrockUsageRoundLog
    from services import usage_service

    await usage_service.record_round_log(
        user_id="usr-1", session_id="s1", model_id=None, round_type="image", fixed_cost_usd=0.04,
        tool_name="generate_image", session_factory=pg_db,
    )
    await usage_service.record_round_log(
        user_id="usr-1", session_id="s1", model_id=HAIKU, round_type="converse", usage=_usage(),
        agent_profile_id="agent_support", session_factory=pg_db,
    )
    async with pg_db() as s:
        a, b = await s.get(BedrockUsageRoundLog, 1), await s.get(BedrockUsageRoundLog, 2)
        assert float(a.estimated_cost_usd) == pytest.approx(0.04)
        assert float(b.estimated_cost_usd) == pytest.approx(6.0)
        assert b.agent_profile_id == "agent_support"


async def test_registro_de_uso_nunca_rompe_el_chat(caplog):
    from services import usage_service

    def _boom():
        raise RuntimeError("bd caída")

    with caplog.at_level(logging.ERROR):
        await usage_service.record_turn_usage("usr-1", "s1", HAIKU, _usage(), session_factory=_boom)
        await usage_service.record_round_log(
            user_id="usr-1", session_id="s1", model_id=HAIKU, round_type="converse", session_factory=_boom
        )
    assert "Failed to record turn usage" in caplog.text
    assert "Failed to record round log" in caplog.text


async def test_presupuesto_disponible_agotado_y_restante(pg_db):
    from repositories import usage_repo
    from services import usage_service

    async with pg_db() as s:
        await usage_service.assert_budget_available(s, "usr-1", 5.0)
        await usage_repo.add_turn_log(
            s, user_id="usr-1", session_id="s", model_id="m", input_tokens=0, output_tokens=0,
            cache_read_tokens=0, cache_write_tokens=0, estimated_cost_usd=3.0,
        )
        await usage_service.assert_budget_available(s, "usr-1", 5.0)
        assert await usage_service.get_remaining_budget_usd(s, "usr-1", 5.0) == pytest.approx(2.0)
        with pytest.raises(usage_service.BudgetExceeded, match=r"\$3\.00 / \$3\.00"):
            await usage_service.assert_budget_available(s, "usr-1", 3.0)
        assert await usage_service.get_remaining_budget_usd(s, "usr-1", 1.0) == 0.0


def test_budget_exceeded_es_un_error_de_proveedor():
    from providers.base import ProviderError
    from services import usage_service

    assert issubclass(usage_service.BudgetExceeded, ProviderError)
    assert usage_service.BedrockBudgetExceeded is usage_service.BudgetExceeded


async def test_metricas_incluyen_ahorro_de_cache_y_presupuesto(pg_db):
    from repositories import usage_repo
    from services import usage_service

    async with pg_db() as s:
        await usage_repo.add_turn_log(
            s, user_id="usr-1", session_id="s", model_id=HAIKU, input_tokens=10, output_tokens=5,
            cache_read_tokens=1_000_000, cache_write_tokens=0, estimated_cost_usd=2.0,
        )
        await usage_repo.add_turn_log(
            s, user_id="usr-1", session_id="s", model_id="desconocido", input_tokens=1, output_tokens=1,
            cache_read_tokens=500, cache_write_tokens=0, estimated_cost_usd=1.0,
        )
        m = await usage_service.get_usage_metrics(s, "usr-1", days=30, daily_budget=10.0)
        assert [x["model_id"] for x in m["by_model"]] == [HAIKU, "desconocido"]
        assert len(m["by_day"]) == 1
        assert m["total_estimated_cost_usd"] == pytest.approx(3.0)
        assert m["total_cache_read_tokens"] == 1_000_500
        # 1M tokens * $1/M * (1 - 0.10); el modelo fuera del catálogo no ahorra nada
        assert m["total_cache_savings_usd"] == pytest.approx(0.9)
        assert m["daily_budget_usd"] == 10.0
        assert m["daily_spent_usd"] == pytest.approx(3.0)
        assert m["daily_remaining_usd"] == pytest.approx(7.0)


def test_ahorro_de_cache_se_deriva_de_estimate_cost_y_coincide_con_la_tabla_de_precios():
    """RF-005: `services/` depende solo del protocolo `ModelProvider` (frontera del proveedor)."""
    from providers.bedrock import pricing
    from services import usage_service

    for model, tokens in ((HAIKU, 1_000_000), (HAIKU, 500), ("desconocido", 1_000_000)):
        assert usage_service.cache_read_savings_usd(model, tokens) == pytest.approx(
            pricing.cache_read_savings_usd(model, tokens)
        )
    assert usage_service.cache_read_savings_usd(HAIKU, 1_000_000) == pytest.approx(0.90)


async def test_coste_y_ahorro_usan_el_provider_inyectado(monkeypatch, pg_db):
    from repositories import usage_repo
    from services import usage_service

    class FakeProvider:
        def estimate_cost(self, model_id, usage):
            return 2.0 * usage.input_tokens + 1.0 * usage.cache_read_tokens

    monkeypatch.setattr(usage_service, "_provider", lambda: FakeProvider())
    assert usage_service.cache_read_savings_usd("m", 3) == pytest.approx(3.0)
    await usage_service.record_turn_usage("usr-1", "s1", "m", Usage(input_tokens=2), session_factory=pg_db)
    async with pg_db() as s:
        m = await usage_service.get_usage_metrics(s, "usr-1", days=7, daily_budget=5.0)
    assert m["total_estimated_cost_usd"] == pytest.approx(4.0)
