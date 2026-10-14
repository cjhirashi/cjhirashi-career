"""RF-003 / RF-004: clientes de archivos, secciones y metodologías (T-034)."""
import httpx
import pytest

from clients.api_client import ApiError
from clients.files import FilesClient
from clients.sections import MethodologiesClient, SectionsClient
from middleware.principal import ServiceContext, service_scope
from tests.unit.clients._helpers import as_user, make_api

pytestmark = [pytest.mark.requisito("RF-003"), pytest.mark.requisito("RF-004")]


async def test_upload_is_multipart_with_form_fields():
    api, rec = make_api(lambda r: httpx.Response(201, json={"id": "f-1"}))
    with as_user():
        out = await FilesClient(api).upload(
            "img.png", b"\x89PNG", "image/png", category="generated", description="d", is_public=False
        )
    assert out == {"id": "f-1"}
    req = rec.last
    assert (req.method, req.url.path) == ("POST", "/files")
    assert req.headers["content-type"].startswith("multipart/form-data")
    body = req.content
    assert b'name="file"; filename="img.png"' in body and b"image/png" in body and b"\x89PNG" in body
    assert b'name="category"' in body and b"generated" in body
    assert b'name="is_public"' in body and b"false" in body


async def test_upload_omits_unset_optional_fields():
    api, rec = make_api(lambda r: httpx.Response(201, json={}))
    with as_user():
        await FilesClient(api).upload("a.txt", b"x", "text/plain")
    assert b'name="category"' not in rec.last.content
    assert b'name="is_public"' not in rec.last.content


async def test_list_get_raw_and_visibility():
    def handler(req):
        if req.url.path.endswith("/raw"):
            return httpx.Response(200, content=b"DATA", headers={"content-type": "image/png"})
        if req.method == "PATCH":
            return httpx.Response(200, json={"id": "f-1", "is_public": False})
        if req.url.path == "/files":
            return httpx.Response(200, json=[{"id": "f-1"}])
        return httpx.Response(200, json={"id": "f-1", "mime_type": "image/png"})

    api, rec = make_api(handler)
    c = FilesClient(api)
    with as_user():
        assert await c.list(category="gen", file_type="image", skip=5, limit=10) == [{"id": "f-1"}]
        assert dict(rec.last.url.params) == {"category": "gen", "file_type": "image", "skip": "5", "limit": "10"}
        assert (await c.get("f-1"))["mime_type"] == "image/png"
        assert rec.last.url.path == "/files/f-1"
        assert await c.get_raw("f-1") == (b"DATA", "image/png")
        assert rec.last.url.path == "/files/f-1/raw"
        await c.set_visibility("f-1", False)
        assert (rec.last.method, rec.last.url.path, rec.last_json()) == ("PATCH", "/files/f-1/visibility", {"is_public": False})


async def test_get_download_url_returns_the_signed_url_with_the_user_credential():
    api, rec = make_api(lambda r: httpx.Response(200, json={"url": "https://signed.test/x?sig=1"}))
    with as_user():
        assert await FilesClient(api).get_download_url("f-1") == "https://signed.test/x?sig=1"
        with pytest.raises(ValueError):
            await FilesClient(api).get_download_url("../x")
    assert len(rec.requests) == 1
    assert (rec.last.method, rec.last.url.path) == ("GET", "/files/f-1/download")
    assert rec.last.headers["authorization"] == "Bearer user-jwt"


async def test_files_rejects_unsafe_ids_and_propagates_errors():
    api, rec = make_api(lambda r: httpx.Response(404, json={"detail": "nope"}))
    c = FilesClient(api)
    with as_user():
        with pytest.raises(ValueError):
            await c.get("../x")
        with pytest.raises(ApiError) as info:
            await c.get("f-1")
    assert info.value.status == 404 and len(rec.requests) == 1


async def test_sections_list_get_update():
    api, rec = make_api(lambda r: httpx.Response(200, json=[{"id": "jobs"}] if r.url.path == "/admin/sections" else {"id": "jobs"}))
    c = SectionsClient(api)
    with as_user():
        assert await c.list() == [{"id": "jobs"}]
        assert rec.last.url.path == "/admin/sections"
        assert await c.get("jobs") == {"id": "jobs"}
        assert rec.last.url.path == "/admin/sections/jobs"
        await c.update("jobs", {"domain": "x", "instructions": "y"})
        assert (rec.last.method, rec.last.url.path) == ("PUT", "/admin/sections/jobs")
        assert rec.last_json() == {"domain": "x", "instructions": "y"}


async def test_sections_work_with_service_context():
    api, rec = make_api(lambda r: httpx.Response(200, json=[]))
    with service_scope(ServiceContext.from_settings()):
        await SectionsClient(api).list()
    assert rec.last.headers["authorization"] == "Bearer test-service-token"


async def test_methodologies_use_career_route():
    api, rec = make_api(lambda r: httpx.Response(200, json=[{"id": "m-1"}] if r.method == "GET" and r.url.path.endswith("methodologies") else {"id": "m-1"}))
    c = MethodologiesClient(api)
    with as_user():
        assert await c.list() == [{"id": "m-1"}]
        assert rec.last.url.path == "/career/operational-methodologies"
        assert await c.get("m-1") == {"id": "m-1"}
        assert rec.last.url.path == "/career/operational-methodologies/m-1"
        await c.update("m-1", {"title": "t"})
        assert (rec.last.method, rec.last.url.path) == ("PUT", "/career/operational-methodologies/m-1")
