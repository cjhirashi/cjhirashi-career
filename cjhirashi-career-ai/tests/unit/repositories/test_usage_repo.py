"""RF-006: repositorio de uso (bedrock_usage_logs / bedrock_usage_round_logs) (T-064)."""
from datetime import datetime, timedelta, timezone

import pytest

pytestmark = pytest.mark.requisito("RF-006")


def _turn(user="usr-1", model="m1", cost=1.0, when=None, inp=100, out=50, cr=0, cw=0, session="s1"):
    d = dict(user_id=user, session_id=session, model_id=model, input_tokens=inp, output_tokens=out,
             cache_read_tokens=cr, cache_write_tokens=cw, estimated_cost_usd=cost)
    if when is not None:
        d["created_at"] = when
    return d


async def test_add_turn_log_persiste_una_fila(pg_db):
    from models import BedrockUsageLog
    from repositories import usage_repo

    async with pg_db() as s:
        await usage_repo.add_turn_log(s, **_turn(cr=7, cw=3))
        row = await s.get(BedrockUsageLog, 1)
        assert (row.user_id, row.model_id, row.input_tokens, row.output_tokens) == ("usr-1", "m1", 100, 50)
        assert (row.cache_read_tokens, row.cache_write_tokens) == (7, 3)
        assert float(row.estimated_cost_usd) == 1.0


async def test_add_round_log_persiste_campos_granulares(pg_db):
    from models import BedrockUsageRoundLog
    from repositories import usage_repo

    async with pg_db() as s:
        await usage_repo.add_round_log(
            s, user_id="usr-1", session_id="s1", model_id=None, round_type="image", tool_name="generate_image",
            agent_profile_id="agent_visual_design", input_tokens=0, output_tokens=0,
            cache_read_tokens=0, cache_write_tokens=0, estimated_cost_usd=0.04, notes="n",
        )
        row = await s.get(BedrockUsageRoundLog, 1)
        assert (row.round_type, row.tool_name, row.agent_profile_id, row.notes) == (
            "image", "generate_image", "agent_visual_design", "n")
        assert row.model_id is None
        assert float(row.estimated_cost_usd) == pytest.approx(0.04)


async def test_gasto_diario_suma_solo_hoy_y_solo_del_usuario(pg_db):
    from repositories import usage_repo

    ahora = datetime.now(timezone.utc)
    async with pg_db() as s:
        assert await usage_repo.sum_cost_since(s, "usr-1", ahora - timedelta(hours=1)) == 0.0
        await usage_repo.add_turn_log(s, **_turn(cost=1.5))
        await usage_repo.add_turn_log(s, **_turn(cost=2.0))
        await usage_repo.add_turn_log(s, **_turn(cost=9.0, when=ahora - timedelta(days=2)))
        await usage_repo.add_turn_log(s, **_turn(user="usr-2", cost=100.0))
        assert await usage_repo.get_daily_spend_usd(s, "usr-1") == pytest.approx(3.5)
        assert await usage_repo.get_daily_spend_usd(s, "usr-2") == pytest.approx(100.0)
        assert await usage_repo.get_daily_spend_usd(s, "usr-3") == 0.0


async def test_gasto_diario_no_cuenta_los_round_logs(pg_db):
    """El presupuesto sale de usage_logs (una fila por turno); sumar rondas duplicaría (ADR-019)."""
    from repositories import usage_repo

    async with pg_db() as s:
        await usage_repo.add_turn_log(s, **_turn(cost=1.0))
        await usage_repo.add_round_log(
            s, user_id="usr-1", session_id="s1", model_id="m1", round_type="converse", tool_name=None,
            agent_profile_id=None, input_tokens=1, output_tokens=1, cache_read_tokens=0,
            cache_write_tokens=0, estimated_cost_usd=50.0, notes=None,
        )
        assert await usage_repo.get_daily_spend_usd(s, "usr-1") == pytest.approx(1.0)


async def test_agregado_por_modelo_ordenado_por_coste(pg_db):
    from repositories import usage_repo

    async with pg_db() as s:
        await usage_repo.add_turn_log(s, **_turn(model="barato", cost=0.5, inp=10, out=1, cr=2, cw=3))
        await usage_repo.add_turn_log(s, **_turn(model="caro", cost=2.0, inp=100, out=10, cr=20, cw=30))
        await usage_repo.add_turn_log(s, **_turn(model="caro", cost=3.0, inp=200, out=20, cr=40, cw=60))
        await usage_repo.add_turn_log(s, **_turn(user="usr-2", model="otro", cost=99.0))
        rows = await usage_repo.usage_by_model(s, "usr-1")
        assert [r["model_id"] for r in rows] == ["caro", "barato"]
        caro = rows[0]
        assert caro == {"model_id": "caro", "input_tokens": 300, "output_tokens": 30, "cache_read_tokens": 60,
                        "cache_write_tokens": 90, "estimated_cost_usd": pytest.approx(5.0), "turns": 2}


async def test_agregado_por_dia_respeta_la_ventana(pg_db):
    from repositories import usage_repo

    ahora = datetime.now(timezone.utc)
    async with pg_db() as s:
        await usage_repo.add_turn_log(s, **_turn(cost=1.0, when=ahora))
        await usage_repo.add_turn_log(s, **_turn(cost=2.0, when=ahora))
        await usage_repo.add_turn_log(s, **_turn(cost=4.0, when=ahora - timedelta(days=3)))
        await usage_repo.add_turn_log(s, **_turn(cost=8.0, when=ahora - timedelta(days=40)))
        corto = await usage_repo.usage_by_day(s, "usr-1", days=7)
        assert [round(r["estimated_cost_usd"], 2) for r in corto] == [4.0, 3.0]
        assert corto[0]["day"] < corto[1]["day"]
        largo = await usage_repo.usage_by_day(s, "usr-1", days=60)
        assert [round(r["estimated_cost_usd"], 2) for r in largo] == [8.0, 4.0, 3.0]
        assert await usage_repo.usage_by_day(s, "usr-2", days=60) == []
