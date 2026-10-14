"""T-050 — autenticación JWT del harness (RF-002, RF-019).

Matriz de `contracts/auth-jwt-service-account.md` §5, fila ai/middleware. Los JWT se firman con el
secreto de test del conftest; ninguna prueba toca red ni la API.
"""
import asyncio
import socket
import time

import httpx
import jwt
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from config import settings
from middleware.auth import require_principal
from middleware.principal import Principal, current_principal

pytestmark = [pytest.mark.requisito("RF-002"), pytest.mark.requisito("RF-019")]


def _sign(secret=None, **claims) -> str:
    payload = {"sub": "user-1", "exp": int(time.time()) + 300}
    payload.update(claims)
    payload = {k: v for k, v in payload.items() if v is not None}
    return jwt.encode(payload, secret or settings.SECRET_KEY, algorithm=settings.ALGORITHM)


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    """Cualquier salida de red (transportes reales de httpx o sockets) hace fallar el test."""

    def _boom(*_a, **_k):
        raise AssertionError("el middleware de auth no debe llamar a la API ni a la red")

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", _boom)
    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", _boom)
    monkeypatch.setattr(socket.socket, "connect", _boom)


@pytest.fixture
def client():
    app = FastAPI()
    calls = []

    @app.get("/probe")
    async def probe(principal: Principal = Depends(require_principal)):
        calls.append(1)
        return {
            "user_id": principal.user_id,
            "token": principal.token,
            "scope_token": current_principal().token,
            "scope_user": current_principal().user_id,
        }

    c = TestClient(app)
    c.calls = calls
    return c


def _get(client, token=None, scheme="Bearer"):
    headers = {} if token is None else {"Authorization": f"{scheme} {token}"}
    return client.get("/probe", headers=headers)


def _assert_rejected(client, resp, status):
    assert resp.status_code == status
    assert client.calls == []  # el handler no se ejecutó: petición no procesada
    assert isinstance(resp.json().get("detail"), str)


def test_sin_header_401(client):
    resp = client.get("/probe")
    _assert_rejected(client, resp, 401)
    assert resp.headers["www-authenticate"] == "Bearer"


def test_esquema_distinto_de_bearer_401(client):
    _assert_rejected(client, _get(client, _sign(), scheme="Basic"), 401)


def test_bearer_sin_token_401(client):
    resp = client.get("/probe", headers={"Authorization": "Bearer "})
    _assert_rejected(client, resp, 401)


def test_firma_invalida_401_sin_filtrar_token(client):
    token = _sign(secret="otro-secreto-distinto-0123456789abcdef0123")
    resp = _get(client, token)
    _assert_rejected(client, resp, 401)
    assert token not in resp.text


def test_expirado_401(client):
    _assert_rejected(client, _get(client, _sign(exp=int(time.time()) - 10)), 401)


def test_refresh_401(client):
    _assert_rejected(client, _get(client, _sign(type="refresh")), 401)


def test_sin_sub_401(client):
    _assert_rejected(client, _get(client, _sign(sub=None)), 401)


def test_algoritmo_none_401(client):
    token = jwt.encode({"sub": "user-1", "exp": int(time.time()) + 300}, None, algorithm="none")
    _assert_rejected(client, _get(client, token), 401)


@pytest.mark.parametrize("role", ["admin", "", 7, ["user"]])
def test_role_desconocido_401(client, role):
    _assert_rejected(client, _get(client, _sign(role=role)), 401)


@pytest.mark.parametrize("role", ["agent", "service"])
def test_role_agent_o_service_403(client, role):
    _assert_rejected(client, _get(client, _sign(role=role)), 403)


def test_sin_claim_role_es_user(client):
    resp = _get(client, _sign())
    assert resp.status_code == 200
    assert resp.json()["user_id"] == "user-1"


def test_token_valido_devuelve_principal_y_lo_deja_en_scope(client):
    token = _sign(role="user", sub="u-42")
    resp = _get(client, token)
    assert resp.status_code == 200
    body = resp.json()
    assert body == {"user_id": "u-42", "token": token, "scope_token": token, "scope_user": "u-42"}


def test_scope_se_limpia_al_terminar_la_request(client):
    _get(client, _sign())
    assert current_principal() is None


def test_error_no_incluye_token_ni_en_logs(client, caplog):
    token = _sign(exp=int(time.time()) - 10)
    with caplog.at_level("DEBUG"):
        resp = _get(client, token)
    assert token not in resp.text
    assert token not in caplog.text


def test_principal_repr_no_expone_token():
    assert "secreto-tok" not in repr(Principal(user_id="u", token="secreto-tok"))


@pytest.mark.parametrize("alg", ["HS384", "HS512"])
def test_confusion_de_algoritmo_401(client, alg):
    token = jwt.encode(
        {"sub": "user-1", "exp": int(time.time()) + 300}, settings.SECRET_KEY, algorithm=alg
    )
    _assert_rejected(client, _get(client, token), 401)


def test_sub_no_str_401(client):
    _assert_rejected(client, _get(client, _sign(sub=123)), 401)


def test_scope_none_si_el_handler_lanza():
    app = FastAPI()

    @app.get("/boom")
    async def boom(_: Principal = Depends(require_principal)):
        raise RuntimeError("fallo del handler")

    c = TestClient(app, raise_server_exceptions=False)
    resp = c.get("/boom", headers={"Authorization": f"Bearer {_sign()}"})
    assert resp.status_code == 500
    assert current_principal() is None


async def test_requests_concurrentes_no_mezclan_principal():
    app = FastAPI()

    @app.get("/who")
    async def who(principal: Principal = Depends(require_principal)):
        await asyncio.sleep(0.01)  # cede el control para forzar intercalado
        return {"user_id": principal.user_id, "scope": current_principal().user_id}

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        responses = await asyncio.gather(
            *[
                ac.get("/who", headers={"Authorization": f"Bearer {_sign(sub=f'u-{i}')}"})
                for i in range(20)
            ]
        )
    for i, r in enumerate(responses):
        assert r.json() == {"user_id": f"u-{i}", "scope": f"u-{i}"}
    assert current_principal() is None


# --- T-052 (D-27): `exp` obligatorio y lista blanca de `type` -------------------------------------


def test_sin_exp_401(client):
    _assert_rejected(client, _get(client, _sign(exp=None)), 401)


@pytest.mark.parametrize("token_type", ["refresh", "linkedin_oauth_state", "otro", "", "ACCESS", 7, ["access"]])
def test_type_distinto_de_access_401(client, token_type):
    _assert_rejected(client, _get(client, _sign(type=token_type)), 401)


def test_type_access_es_aceptado(client):
    resp = _get(client, _sign(type="access", sub="u-7"))
    assert resp.status_code == 200
    assert resp.json()["user_id"] == "u-7"


def test_type_ausente_es_aceptado(client):
    resp = _get(client, _sign())  # `_sign` no emite `type`: token anterior al despliegue
    assert resp.status_code == 200
