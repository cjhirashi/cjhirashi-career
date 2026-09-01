"""El gasto diario se cuenta una sola vez: solo bedrock_usage_logs, no + round_logs.

Regresión: `get_daily_spend_usd` sumaba bedrock_usage_logs + bedrock_usage_round_logs,
que son el mismo gasto a distinta granularidad → doble conteo (ADR-019).
"""
import inspect

import pytest

from services.bedrock import budget
from services.bedrock.budget import get_daily_spend_usd


class _FakeResult:
    def __init__(self, value):
        self._value = value

    def scalar_one(self):
        return self._value


class _FakeSession:
    """Registra cada select ejecutado y devuelve un costo fijo por consulta."""

    def __init__(self, per_query_cost):
        self._cost = per_query_cost
        self.executions = 0

    async def execute(self, _stmt):
        self.executions += 1
        return _FakeResult(self._cost)


@pytest.mark.asyncio
async def test_daily_spend_runs_a_single_query_over_usage_logs():
    db = _FakeSession(per_query_cost=0.30)
    spent = await get_daily_spend_usd(db, "usr-1")

    # Una sola consulta (antes eran dos: turn + round → 0.30 + 0.30 = 0.60).
    assert db.executions == 1
    assert spent == pytest.approx(0.30)


@pytest.mark.asyncio
async def test_daily_spend_zero_when_no_rows():
    db = _FakeSession(per_query_cost=0)
    assert await get_daily_spend_usd(db, "usr-1") == 0.0


def test_budget_module_no_longer_imports_round_log():
    src = inspect.getsource(budget)
    assert "BedrockUsageRoundLog" not in src
