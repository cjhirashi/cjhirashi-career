"""RF-004: endurecimiento del cliente REST (menores del revisor, bloque C)."""
import httpx
import pytest

from clients.api_client import ApiClient, MissingCredentialError
from clients.errors import ErrorsClient
from config import settings
from middleware.principal import Principal, ServiceContext, principal_scope, service_scope
from tests.unit.clients._helpers import make_api

pytestmark = pytest.mark.requisito("RF-004")


def test_repr_never_contains_the_token():
    assert "s3cr3t" not in repr(Principal(user_id="u", token="s3cr3t"))
    assert "s3cr3t" not in repr(ServiceContext(token="s3cr3t"))


@pytest.mark.parametrize("blank", ["", "   ", "\t\n"])
async def test_blank_principal_token_is_missing_credential(blank):
    api, rec = make_api()
    with principal_scope(Principal(user_id="u", token=blank)), pytest.raises(MissingCredentialError):
        await api.get_json("/x")
    assert rec.requests == []


@pytest.mark.parametrize("blank", ["", "  "])
async def test_blank_service_token_is_missing_credential(monkeypatch, blank):
    monkeypatch.setattr(settings, "AI_SERVICE_TOKEN", blank)
    api, rec = make_api()
    with pytest.raises(MissingCredentialError):
        await api.post_json("/notifications", json={}, auth="service")
    with service_scope(ServiceContext.from_settings()), pytest.raises(MissingCredentialError):
        await api.get_json("/x")
    assert rec.requests == []


async def test_explicit_timeout_zero_is_respected():
    api = ApiClient(timeout=0)
    assert api._client.timeout.read == 0
    await api.aclose()


async def test_cookies_are_not_kept_between_requests():
    seen = []

    def handler(req):
        seen.append(req.headers.get("cookie"))
        return httpx.Response(200, json={}, headers={"set-cookie": "sid=abc; Path=/"})

    api, _ = make_api(handler)
    with principal_scope(Principal(user_id="u", token="t")):
        await api.get_json("/a")
        await api.get_json("/b")
    assert seen == [None, None]


async def test_error_report_never_raises_on_unserializable_payload():
    api, rec = make_api()
    assert await ErrorsClient(api).report({"x": object()}) is False
    assert rec.requests == []
