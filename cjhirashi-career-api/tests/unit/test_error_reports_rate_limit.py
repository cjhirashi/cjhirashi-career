"""Unit test del rate-limit en memoria del endpoint público `POST /system/error-report`."""
import importlib

import pytest


@pytest.fixture
def routes_module():
    mod = importlib.import_module("routes.error_reports")
    # Estado limpio por test.
    mod._ingest_hits.clear()
    return mod


def test_permite_hasta_el_limite_y_luego_bloquea(routes_module):
    mod = routes_module
    ip = "203.0.113.7"
    allowed = sum(0 if mod._rate_limited(ip) else 1 for _ in range(mod._INGEST_MAX_PER_WINDOW))
    assert allowed == mod._INGEST_MAX_PER_WINDOW
    # El siguiente ya excede la ventana.
    assert mod._rate_limited(ip) is True


def test_ips_distintas_no_se_afectan(routes_module):
    mod = routes_module
    for _ in range(mod._INGEST_MAX_PER_WINDOW):
        mod._rate_limited("198.51.100.1")
    assert mod._rate_limited("198.51.100.1") is True
    assert mod._rate_limited("198.51.100.2") is False
