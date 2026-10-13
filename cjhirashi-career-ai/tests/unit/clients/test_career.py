"""RF-003: cliente del CRUD genérico de carrera (T-032)."""
import json

import httpx
import pytest

from clients.api_client import ApiError
from clients.career import CareerClient, LocalResourceError
from tests.unit.clients._helpers import as_user, make_api

pytestmark = pytest.mark.requisito("RF-003")


def _q(req):
    return dict(req.url.params)


async def test_list_single_page_with_query_params():
    api, rec = make_api(lambda r: httpx.Response(200, json=[{"id": "a"}]))
    with as_user():
        out = await CareerClient(api).list(
            "projects", search="x", filters={"status": "open"}, sort_by="name", sort_dir="desc"
        )
    assert out == [{"id": "a"}]
    assert rec.last.url.path == "/career/projects"
    q = _q(rec.last)
    assert q["search"] == "x" and q["sort_by"] == "name" and q["sort_dir"] == "desc"
    assert json.loads(q["filters"]) == {"status": "open"}
    assert q["skip"] == "0" and q["limit"] == "100"


async def test_list_paginates_until_short_page():
    pages = {0: [{"id": i} for i in range(100)], 100: [{"id": i} for i in range(100, 130)]}
    api, rec = make_api(lambda r: httpx.Response(200, json=pages[int(r.url.params["skip"])]))
    with as_user():
        out = await CareerClient(api).list("projects")
    assert len(out) == 130
    assert [_q(r)["skip"] for r in rec.requests] == ["0", "100"]


async def test_list_respects_the_hard_cap_and_explicit_limit():
    api, rec = make_api(lambda r: httpx.Response(200, json=[{"id": i} for i in range(int(r.url.params["limit"]))]))
    with as_user():
        out = await CareerClient(api, max_items=150).list("projects")
        assert len(out) == 150
        assert [_q(r)["limit"] for r in rec.requests] == ["100", "50"]
        out = await CareerClient(api, max_items=150).list("projects", limit=10)
        assert len(out) == 10
        out = await CareerClient(api, max_items=150).list("projects", limit=9999)
        assert len(out) == 150


async def test_get_create_update_delete():
    api, rec = make_api(lambda r: httpx.Response(204) if r.method == "DELETE" else httpx.Response(200, json={"id": "p-1"}))
    c = CareerClient(api)
    with as_user():
        assert await c.get("projects", "p-1") == {"id": "p-1"}
        assert (rec.last.method, rec.last.url.path) == ("GET", "/career/projects/p-1")
        await c.create("projects", {"name": "n"})
        assert (rec.last.method, rec.last.url.path, rec.last_json()) == ("POST", "/career/projects", {"name": "n"})
        await c.update("projects", "p-1", {"name": "m"})
        assert (rec.last.method, rec.last.url.path, rec.last_json()) == ("PUT", "/career/projects/p-1", {"name": "m"})
        assert await c.delete("projects", "p-1") is None
        assert (rec.last.method, rec.last.url.path) == ("DELETE", "/career/projects/p-1")


async def test_count_and_distinct():
    def handler(req):
        if req.url.path.endswith("/count"):
            return httpx.Response(200, json={"count": 7})
        return httpx.Response(200, json={"field": "status", "values": ["a", "b"]})

    api, rec = make_api(handler)
    c = CareerClient(api)
    with as_user():
        assert await c.count("projects", search="s", filters={"k": 1}) == 7
        assert rec.last.url.path == "/career/projects/count"
        assert json.loads(_q(rec.last)["filters"]) == {"k": 1}
        assert await c.distinct("projects", "status") == ["a", "b"]
        assert rec.last.url.path == "/career/projects/distinct/status"


async def test_bulk_update_is_n_sequential_puts_and_collects_failures():
    def handler(req):
        if req.url.path.endswith("/p-2"):
            return httpx.Response(404, json={"detail": "no existe"})
        return httpx.Response(200, json={"id": req.url.path.rsplit("/", 1)[1]})

    api, rec = make_api(handler)
    with as_user():
        result = await CareerClient(api).bulk_update("projects", [("p-1", {"a": 1}), ("p-2", {"a": 1}), ("p-3", {"a": 2})])
    assert [r.method for r in rec.requests] == ["PUT", "PUT", "PUT"]
    assert [r["ok"] for r in result] == [True, False, True]
    assert result[1]["error"] == "no existe" and result[1]["id"] == "p-2"


async def test_resource_key_routing_to_non_career_paths():
    api, rec = make_api(lambda r: httpx.Response(200, json=[]))
    c = CareerClient(api)
    with as_user():
        await c.list("pdf-output-templates")
        assert rec.last.url.path == "/pdf-templates"
        await c.get("pdf-template-styles", "s-1")
        assert rec.last.url.path == "/pdf-template-styles/s-1"
        await c.list("pdf-template-styles", limit=5)
        assert rec.last.url.path == "/pdf-template-styles"


async def test_agent_tasks_is_local_not_remote():
    api, rec = make_api()
    with pytest.raises(LocalResourceError):
        await CareerClient(api).list("agent-tasks")
    assert rec.requests == []


async def test_unsupported_operations_on_non_career_resources():
    api, rec = make_api()
    c = CareerClient(api)
    with as_user():
        with pytest.raises(ValueError):
            await c.count("pdf-output-templates")
        with pytest.raises(ValueError):
            await c.distinct("pdf-template-styles", "name")
        with pytest.raises(ValueError):
            await c.list("pdf-template-styles", search="x")
    assert rec.requests == []


@pytest.mark.parametrize("bad", ["../users", "a/b", "", "A B", "x?y"])
async def test_invalid_resource_or_id_is_rejected_before_any_request(bad):
    api, rec = make_api()
    c = CareerClient(api)
    with as_user():
        with pytest.raises(ValueError):
            await c.list(bad)
        with pytest.raises(ValueError):
            await c.get("projects", bad)
    assert rec.requests == []


async def test_api_errors_propagate():
    api, _ = make_api(lambda r: httpx.Response(403, json={"detail": "no"}))
    with as_user(), pytest.raises(ApiError) as info:
        await CareerClient(api).get("projects", "p-1")
    assert info.value.status == 403
