"""RF-008: ciclo de vida de la sesión async (get_db) y cierre del engine (T-013)."""
import pytest
from fastapi.testclient import TestClient


@pytest.mark.requisito("RF-008")
async def test_get_db_yields_session_and_closes_on_success():
    from database import get_db

    gen = get_db()
    session = await gen.__anext__()
    assert session.is_active
    with pytest.raises(StopAsyncIteration):
        await gen.__anext__()


@pytest.mark.requisito("RF-008")
async def test_get_db_rolls_back_and_reraises_on_error(monkeypatch):
    import database

    calls = []

    class FakeSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            calls.append("close")

        async def commit(self):
            calls.append("commit")

        async def rollback(self):
            calls.append("rollback")

    monkeypatch.setattr(database, "AsyncSessionLocal", lambda: FakeSession())
    gen = database.get_db()
    await gen.__anext__()
    with pytest.raises(RuntimeError, match="boom"):
        await gen.athrow(RuntimeError("boom"))
    assert calls == ["rollback", "close"]


@pytest.mark.requisito("RF-008")
def test_lifespan_disposes_engine_on_shutdown(monkeypatch):
    import app as app_module

    closed = []

    async def fake_close():
        closed.append(True)

    monkeypatch.setattr(app_module, "close_db", fake_close)
    with TestClient(app_module.app) as client:
        assert client.get("/health").status_code == 200
    assert closed == [True]
