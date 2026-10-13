"""RF-003: clientes de LinkedIn, PDF, descubrimiento de vacantes y reporte de errores (T-036)."""
import httpx
import pytest

from clients.errors import ErrorsClient
from clients.job_discovery import JobDiscoveryClient
from clients.linkedin import LinkedInClient
from clients.pdf import PdfClient
from tests.unit.clients._helpers import as_user, make_api

pytestmark = pytest.mark.requisito("RF-003")


async def test_linkedin_routes():
    api, rec = make_api(lambda r: httpx.Response(204) if r.method == "DELETE" else httpx.Response(200, json={"ok": 1}))
    c = LinkedInClient(api)
    with as_user():
        await c.status()
        assert (rec.last.method, rec.last.url.path) == ("GET", "/linkedin/status")
        await c.list_posts()
        assert (rec.last.method, rec.last.url.path) == ("GET", "/linkedin/posts")
        await c.create_post({"content": "hola"})
        assert (rec.last.method, rec.last.url.path, rec.last_json()) == ("POST", "/linkedin/posts", {"content": "hola"})
        assert await c.delete_post("lp-1") is None
        assert (rec.last.method, rec.last.url.path) == ("DELETE", "/linkedin/posts/lp-1")


async def test_pdf_templates_crud_render_and_default():
    def handler(req):
        if req.url.path.endswith("/render"):
            return httpx.Response(200, content=b"%PDF-1", headers={"content-type": "application/pdf"})
        if req.method == "DELETE":
            return httpx.Response(204)
        return httpx.Response(200, json=[{"id": "t"}] if req.url.path == "/pdf-templates" else {"id": "t"})

    api, rec = make_api(handler)
    c = PdfClient(api)
    with as_user():
        assert await c.list_templates(document_type="cv", skip=2, limit=10) == [{"id": "t"}]
        assert dict(rec.last.url.params) == {"document_type": "cv", "skip": "2", "limit": "10"}
        await c.get_template("t")
        assert rec.last.url.path == "/pdf-templates/t"
        await c.default_template("cv")
        assert (rec.last.url.path, dict(rec.last.url.params)) == ("/pdf-templates/defaults/by-type", {"document_type": "cv"})
        await c.create_template({"name": "n"})
        assert (rec.last.method, rec.last.url.path) == ("POST", "/pdf-templates")
        await c.update_template("t", {"name": "m"})
        assert (rec.last.method, rec.last.url.path) == ("PUT", "/pdf-templates/t")
        await c.delete_template("t")
        assert (rec.last.method, rec.last.url.path) == ("DELETE", "/pdf-templates/t")
        assert await c.render_template("t", {"data": {}}) == (b"%PDF-1", "application/pdf")
        assert (rec.last.method, rec.last.url.path, rec.last_json()) == ("POST", "/pdf-templates/t/render", {"data": {}})


async def test_pdf_styles_crud():
    api, rec = make_api(lambda r: httpx.Response(204) if r.method == "DELETE" else httpx.Response(200, json={"id": "s"}))
    c = PdfClient(api)
    with as_user():
        await c.list_styles(limit=5)
        assert (rec.last.url.path, dict(rec.last.url.params)) == ("/pdf-template-styles", {"skip": "0", "limit": "5"})
        await c.get_style("s")
        assert rec.last.url.path == "/pdf-template-styles/s"
        await c.create_style({"name": "n"})
        assert (rec.last.method, rec.last.url.path) == ("POST", "/pdf-template-styles")
        await c.update_style("s", {"name": "m"})
        assert (rec.last.method, rec.last.url.path) == ("PUT", "/pdf-template-styles/s")
        await c.delete_style("s")
        assert (rec.last.method, rec.last.url.path) == ("DELETE", "/pdf-template-styles/s")


async def test_job_discovery_routes():
    api, rec = make_api(lambda r: httpx.Response(200, json={"ok": 1}))
    c = JobDiscoveryClient(api)
    with as_user():
        await c.providers()
        assert (rec.last.method, rec.last.url.path) == ("GET", "/career/job-discoveries/providers")
        await c.run({"query": "python"})
        assert (rec.last.method, rec.last.url.path, rec.last_json()) == ("POST", "/career/job-discoveries/run", {"query": "python"})
        await c.import_url({"url": "http://x"})
        assert rec.last.url.path == "/career/job-discoveries/import-url"
        await c.save({"listings": []})
        assert rec.last.url.path == "/career/job-discoveries/save"


async def test_error_report_needs_no_credential_and_returns_true():
    api, rec = make_api(lambda r: httpx.Response(202, json={"accepted": True}))
    assert await ErrorsClient(api).report({"message": "boom"}) is True  # sin Principal ni ServiceContext
    assert (rec.last.method, rec.last.url.path) == ("POST", "/system/error-report")
    assert "authorization" not in rec.last.headers
    assert rec.last_json() == {"message": "boom"}


@pytest.mark.parametrize("response", [httpx.Response(429, json={"detail": "rate"}), httpx.Response(503)])
async def test_error_report_never_raises(response):
    api, _ = make_api(lambda r: response)
    assert await ErrorsClient(api).report({"message": "boom"}) is False


async def test_error_report_swallows_transport_failures():
    def handler(req):
        raise httpx.ConnectError("caída", request=req)

    api, _ = make_api(handler)
    assert await ErrorsClient(api).report({"message": "boom"}) is False
