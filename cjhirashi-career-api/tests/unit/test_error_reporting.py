"""Unit tests del camino de escritura del registro de fallas (ADR-018).

Cubren la lógica pura (normalización, huella, guard de recursión, context
manager). La deduplicación contra una fila real y los endpoints necesitan un
Postgres de pruebas (la infra de tests del repo es SQLite y `error_reports`
usa JSONB + secuencia) — queda como gap documentado.
"""
import pytest

from services import error_reporting
from services.error_reporting import (
    _fingerprint,
    _normalize,
    capture_errors,
    report_error,
)


class TestNormalize:
    def test_colapsa_numeros_uuid_y_espacios(self):
        a = _normalize("Fila 12345 no encontrada  (id=ab12cd34-0000-1111-2222-333344445555)")
        b = _normalize("Fila 999 no encontrada (id=ff00aa11-9999-8888-7777-666655554444)")
        assert a == b
        assert "<n>" in a and "<uuid>" in a

    def test_trunca_a_500(self):
        assert len(_normalize("x" * 5000)) == 500


class TestFingerprint:
    def test_misma_falla_misma_huella(self):
        fp1 = _fingerprint("api:POST /x", "ValueError", "algo falló en el registro 5")
        fp2 = _fingerprint("api:POST /x", "ValueError", "algo falló en el registro 981")
        assert fp1 == fp2

    def test_distinto_source_distinta_huella(self):
        fp1 = _fingerprint("api:POST /x", "ValueError", "boom")
        fp2 = _fingerprint("api:POST /y", "ValueError", "boom")
        assert fp1 != fp2

    def test_es_sha256_hex(self):
        fp = _fingerprint("s", None, "m")
        assert len(fp) == 64 and all(c in "0123456789abcdef" for c in fp)


class TestRecursionGuard:
    def test_no_toca_la_bd_si_ya_esta_registrando(self, monkeypatch):
        llamado = False

        def _boom():
            nonlocal llamado
            llamado = True
            raise AssertionError("no debería abrir sesión de forma reentrante")

        monkeypatch.setattr(error_reporting, "_SyncSession", _boom)
        token = error_reporting._in_reporting.set(True)
        try:
            report_error("x", "test:guard")  # no debe lanzar ni llamar _SyncSession
        finally:
            error_reporting._in_reporting.reset(token)
        assert llamado is False

    def test_nunca_propaga_si_falla_la_sesion(self, monkeypatch):
        def _boom():
            raise RuntimeError("BD caída")

        monkeypatch.setattr(error_reporting, "_SyncSession", _boom)
        # No debe lanzar: el camino de reporte está blindado.
        report_error("original", "test:blindaje", severity="critical")
        # El guard queda liberado para la siguiente llamada.
        assert error_reporting._in_reporting.get() is False


class TestCaptureErrors:
    def test_reraise_true_propaga_y_registra(self, monkeypatch):
        registrado = {}

        def _fake_report(message, source, **kwargs):
            registrado["message"] = message
            registrado["source"] = source
            registrado["severity"] = kwargs.get("severity")

        monkeypatch.setattr(error_reporting, "report_error", _fake_report)

        with pytest.raises(ValueError):
            with capture_errors("test:bloque", severity="warning"):
                raise ValueError("explota")

        assert registrado["source"] == "test:bloque"
        assert registrado["severity"] == "warning"
        assert "explota" in registrado["message"]

    def test_reraise_false_traga_la_excepcion(self, monkeypatch):
        monkeypatch.setattr(error_reporting, "report_error", lambda *a, **k: None)
        with capture_errors("test:bloque", reraise=False):
            raise RuntimeError("silenciado")
        # llega aquí sin propagar
