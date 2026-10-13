"""RF-020 / RF-021: notificaciones (token de servicio) y auditoría (JWT del usuario) (T-038)."""
import httpx
import pytest

from clients.api_client import ApiError
from clients.audit import AuditClient
from clients.notifications import NotificationsClient
from tests.unit.clients._helpers import as_user, make_api


@pytest.mark.requisito("RF-020")
async def test_notification_uses_service_token_even_in_a_user_turn():
    api, rec = make_api(lambda r: httpx.Response(201, json={"id": "ntf-1"}))
    with as_user():
        out = await NotificationsClient(api).create(
            user_id="usr-1", title="Tu turno", body="revisa", kind="task_turn", resource_key="agent-tasks", resource_id="bt-1"
        )
    assert out == {"id": "ntf-1"}
    assert (rec.last.method, rec.last.url.path) == ("POST", "/notifications")
    assert rec.last.headers["authorization"] == "Bearer test-service-token"
    assert rec.last_json() == {
        "user_id": "usr-1", "kind": "task_turn", "title": "Tu turno", "body": "revisa",
        "resource_key": "agent-tasks", "resource_id": "bt-1",
    }


@pytest.mark.requisito("RF-020")
async def test_notification_works_without_any_context_and_omits_unset_fields():
    api, rec = make_api(lambda r: httpx.Response(201, json={}))
    await NotificationsClient(api).create(user_id="usr-1", title="t")
    assert rec.last_json() == {"user_id": "usr-1", "kind": "task_turn", "title": "t"}


@pytest.mark.requisito("RF-020")
async def test_notification_post_is_not_retried_and_403_is_typed():
    api, rec = make_api(lambda r: httpx.Response(403, json={"detail": "solo service"}))
    with pytest.raises(ApiError) as info:
        await NotificationsClient(api).create(user_id="u", title="t")
    assert info.value.status == 403 and len(rec.requests) == 1


@pytest.mark.requisito("RF-021")
async def test_audit_list_and_restore_use_the_user_jwt():
    api, rec = make_api(lambda r: httpx.Response(200, json=[{"id": "aud-1"}] if r.method == "GET" else {"restored": True}))
    c = AuditClient(api)
    with as_user():
        assert await c.list(limit=10, offset=20, resource="projects") == [{"id": "aud-1"}]
        assert (rec.last.method, rec.last.url.path) == ("GET", "/audit-log")
        assert dict(rec.last.url.params) == {"limit": "10", "offset": "20", "resource": "projects"}
        assert rec.last.headers["authorization"] == "Bearer user-jwt"
        assert await c.restore("aud-1") == {"restored": True}
        assert (rec.last.method, rec.last.url.path) == ("POST", "/audit-log/aud-1/restore")
        assert rec.last.headers["authorization"] == "Bearer user-jwt"


@pytest.mark.requisito("RF-021")
@pytest.mark.parametrize("status", [404, 409])
async def test_audit_restore_errors_are_typed(status):
    api, _ = make_api(lambda r: httpx.Response(status, json={"detail": "x"}))
    with as_user(), pytest.raises(ApiError) as info:
        await AuditClient(api).restore("aud-1")
    assert info.value.status == status


@pytest.mark.requisito("RF-021")
async def test_audit_defaults_and_unsafe_id():
    api, rec = make_api(lambda r: httpx.Response(200, json=[]))
    with as_user():
        await AuditClient(api).list()
        assert dict(rec.last.url.params) == {"limit": "50", "offset": "0"}
        with pytest.raises(ValueError):
            await AuditClient(api).restore("../x")
