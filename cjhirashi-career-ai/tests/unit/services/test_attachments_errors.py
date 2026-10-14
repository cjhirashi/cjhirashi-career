"""T-084b (delta del revisor) — `services/attachments.py` (RF-005): sólo el 404 y el id inseguro se
traducen a "Adjunto no encontrado"; cualquier otro `ValueError` (p. ej. 200 con cuerpo no JSON) se propaga."""
import importlib

import httpx
import pytest

from clients import api_client
from providers.base import ProviderError
from tests.unit.clients._helpers import as_user, make_api

pytestmark = pytest.mark.requisito("RF-005")


class Db:
    """`db` no se usa."""


async def build(attachments_):
    attachments = importlib.import_module("services.attachments")
    with as_user():
        return await attachments.build_user_content_blocks(Db(), "u1", "x", attachments_)


async def test_non_json_200_on_metadata_propagates_as_value_error_not_as_not_found(monkeypatch):
    api, rec = make_api(lambda r: httpx.Response(200, content=b"<html>no json</html>"))
    monkeypatch.setattr(api_client, "_default", api)
    with pytest.raises(ValueError) as info:
        await build([{"file_id": "f1"}])
    assert not isinstance(info.value, ProviderError)
    assert "Adjunto no encontrado" not in str(info.value)
    assert [r.url.path for r in rec.requests] == ["/files/f1"]


async def test_unsafe_id_is_still_not_found_without_any_request(monkeypatch):
    api, rec = make_api(lambda r: httpx.Response(200, json={}))
    monkeypatch.setattr(api_client, "_default", api)
    with pytest.raises(ProviderError) as info:
        await build([{"file_id": "../admin"}])
    assert str(info.value) == "Adjunto no encontrado: file_id=../admin"
    assert rec.requests == []
