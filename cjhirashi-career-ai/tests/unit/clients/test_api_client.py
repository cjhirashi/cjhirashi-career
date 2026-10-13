"""RF-004 / RF-003: cliente HTTP único hacia la API (T-030)."""
import httpx
import pytest

from clients.api_client import ApiClient, ApiError, MissingCredentialError
from middleware.principal import ServiceContext, current_principal, service_scope
from tests.unit.clients._helpers import USER, as_user, make_api

pytestmark = pytest.mark.requisito("RF-004")


async def test_user_turn_forwards_the_user_bearer():
    api, rec = make_api()
    with as_user():
        await api.get_json("/career/projects")
    assert rec.last.headers["authorization"] == "Bearer user-jwt"
    assert str(rec.last.url) == "http://api.test/career/projects"


async def test_service_context_uses_ai_service_token():
    api, rec = make_api()
    with service_scope(ServiceContext.from_settings()):
        await api.get_json("/career/projects")
    assert rec.last.headers["authorization"] == "Bearer test-service-token"


async def test_principal_wins_over_service_context():
    api, rec = make_api()
    with service_scope(ServiceContext.from_settings()), as_user():
        await api.get_json("/x")
    assert rec.last.headers["authorization"] == "Bearer user-jwt"


async def test_without_context_raises_missing_credential_and_sends_nothing():
    api, rec = make_api()
    with pytest.raises(MissingCredentialError):
        await api.get_json("/career/projects")
    assert rec.requests == []


async def test_scopes_restore_previous_context():
    assert current_principal() is None
    with as_user():
        assert current_principal() == USER
    assert current_principal() is None


async def test_auth_none_sends_no_authorization():
    api, rec = make_api()
    await api.post_json("/system/error-report", json={"a": 1}, auth="none")
    assert "authorization" not in rec.last.headers


async def test_auth_service_uses_token_even_inside_a_user_turn():
    api, rec = make_api()
    with as_user():
        await api.post_json("/notifications", json={"a": 1}, auth="service")
    assert rec.last.headers["authorization"] == "Bearer test-service-token"


async def test_unknown_auth_mode_is_rejected():
    api, _ = make_api()
    with pytest.raises(ValueError):
        await api.get_json("/x", auth="otro")


@pytest.mark.parametrize("status", [401, 403, 404, 409, 422])
async def test_client_errors_map_to_api_error_without_retry(status):
    api, rec = make_api(lambda r: httpx.Response(status, json={"detail": "motivo"}))
    with as_user(), pytest.raises(ApiError) as info:
        await api.get_json("/career/projects/x")
    assert info.value.status == status
    assert info.value.detail == "motivo"
    assert len(rec.requests) == 1


async def test_error_detail_falls_back_to_text_and_structured_detail():
    api, _ = make_api(lambda r: httpx.Response(422, json={"detail": [{"loc": ["body"], "msg": "x"}]}))
    with as_user(), pytest.raises(ApiError) as info:
        await api.get_json("/x")
    assert info.value.detail == [{"loc": ["body"], "msg": "x"}]
    api, _ = make_api(lambda r: httpx.Response(409, text="conflicto"))
    with as_user(), pytest.raises(ApiError) as info:
        await api.get_json("/x")
    assert info.value.detail == "conflicto"
    assert "409" in str(info.value)


async def test_idempotent_get_retries_5xx_then_succeeds():
    answers = iter([503, 502, 200])

    def handler(req):
        code = next(answers)
        return httpx.Response(code, json={"ok": True})

    api, rec = make_api(handler)
    with as_user():
        assert await api.get_json("/x") == {"ok": True}
    assert len(rec.requests) == 3  # 1 intento + 2 reintentos


async def test_retries_are_capped_at_two():
    api, rec = make_api(lambda r: httpx.Response(500, json={"detail": "boom"}))
    with as_user(), pytest.raises(ApiError) as info:
        await api.get_json("/x")
    assert info.value.status == 500
    assert len(rec.requests) == 3


@pytest.mark.parametrize("method", ["put_json", "delete_json"])
async def test_put_and_delete_are_idempotent_and_retry(method):
    api, rec = make_api(lambda r: httpx.Response(503, json={}))
    with as_user(), pytest.raises(ApiError):
        await getattr(api, method)("/x")
    assert len(rec.requests) == 3


@pytest.mark.parametrize("method", ["post_json", "patch_json"])
async def test_non_idempotent_methods_never_retry(method):
    api, rec = make_api(lambda r: httpx.Response(503, json={}))
    with as_user(), pytest.raises(ApiError):
        await getattr(api, method)("/x")
    assert len(rec.requests) == 1


async def test_timeout_retries_on_get_and_surfaces_api_error():
    def handler(req):
        raise httpx.ReadTimeout("lento", request=req)

    api, rec = make_api(handler)
    with as_user(), pytest.raises(ApiError) as info:
        await api.get_json("/x")
    assert info.value.status == 0
    assert len(rec.requests) == 3


async def test_timeout_on_post_is_not_retried():
    def handler(req):
        raise httpx.ConnectError("sin ruta", request=req)

    api, rec = make_api(handler)
    with as_user(), pytest.raises(ApiError):
        await api.post_json("/x", json={})
    assert len(rec.requests) == 1


async def test_204_returns_none_and_bytes_helpers():
    api, _ = make_api(lambda r: httpx.Response(204))
    with as_user():
        assert await api.delete_json("/x") is None
    api, _ = make_api(lambda r: httpx.Response(200, content=b"%PDF", headers={"content-type": "application/pdf"}))
    with as_user():
        body, ctype = await api.get_bytes("/files/f/raw")
        assert (body, ctype) == (b"%PDF", "application/pdf")
        body, ctype = await api.post_bytes("/pdf-templates/t/render", json={})
        assert body == b"%PDF"


async def test_default_client_uses_settings_and_closes():
    api = ApiClient()
    assert str(api.base_url).rstrip("/") == "http://api.test"
    await api.aclose()
    await api.aclose()  # idempotente


def test_get_api_client_is_a_singleton():
    from clients import api_client

    api_client._default = None
    assert api_client.get_api_client() is api_client.get_api_client()
    api_client._default = None
