"""RF-001: ajustes de runtime del agente: fila de BD con respaldo en config (T-070)."""
from types import SimpleNamespace

import pytest

from config import settings

pytestmark = pytest.mark.requisito("RF-001")


def _row(**kw):
    base = dict(
        active_model_id=None, orchestrator_model_id=None, max_round_trips=3,
        history_window=7, daily_budget_usd="2.5",
    )
    base.update(kw)
    return SimpleNamespace(**base)


async def _load(monkeypatch, row):
    from services import settings_loader

    async def fake_get(db):
        return row

    monkeypatch.setattr(settings_loader.settings_repo, "get_settings", fake_get)
    return await settings_loader.get_runtime_settings(None)


async def test_sin_fila_usa_los_defaults_de_config(monkeypatch):
    rs = await _load(monkeypatch, None)
    assert rs.active_model_id == settings.BEDROCK_DEFAULT_MODEL_ID
    assert rs.orchestrator_model_id == settings.BEDROCK_ORCHESTRATOR_MODEL_ID
    assert rs.max_round_trips == settings.BEDROCK_MAX_ROUND_TRIPS == 6
    assert rs.history_window == settings.BEDROCK_HISTORY_WINDOW == 20
    assert rs.daily_budget_usd == settings.BEDROCK_DAILY_BUDGET_USD == 5.0


async def test_fila_con_valores_prevalece_y_el_presupuesto_es_float(monkeypatch):
    rs = await _load(monkeypatch, _row(active_model_id="m-activo", orchestrator_model_id="m-orq"))
    assert (rs.active_model_id, rs.orchestrator_model_id) == ("m-activo", "m-orq")
    assert (rs.max_round_trips, rs.history_window) == (3, 7)
    assert rs.daily_budget_usd == 2.5 and isinstance(rs.daily_budget_usd, float)


async def test_modelos_nulos_o_vacios_caen_al_default(monkeypatch):
    rs = await _load(monkeypatch, _row(active_model_id="", orchestrator_model_id=None))
    assert rs.active_model_id == settings.BEDROCK_DEFAULT_MODEL_ID
    assert rs.orchestrator_model_id == settings.BEDROCK_ORCHESTRATOR_MODEL_ID


async def test_contra_bd_real(pg_db):
    from repositories import settings_repo
    from services.settings_loader import get_active_model_id, get_runtime_settings

    async with pg_db() as s:
        assert (await get_runtime_settings(s)).active_model_id == settings.BEDROCK_DEFAULT_MODEL_ID
        await settings_repo.set_active_model_id(s, "m-x")
        assert await get_active_model_id(s) == "m-x"
