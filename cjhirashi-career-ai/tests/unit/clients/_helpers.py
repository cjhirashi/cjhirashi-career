"""Utilidades de los tests de clientes REST: transporte simulado, sin red (RNF-001)."""
import json
from typing import Callable, List

import httpx

from clients.api_client import ApiClient
from middleware.principal import Principal, principal_scope

USER = Principal(user_id="usr-1", token="user-jwt")


class Recorder:
    """Transporte simulado que registra las peticiones y responde con `handler`."""

    def __init__(self, handler: Callable[[httpx.Request], httpx.Response] | None = None):
        self.requests: List[httpx.Request] = []
        self._handler = handler or (lambda req: httpx.Response(200, json={}))

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return self._handler(request)

    @property
    def last(self) -> httpx.Request:
        return self.requests[-1]

    def last_json(self):
        return json.loads(self.last.content)


def make_api(handler=None, **kw):
    rec = Recorder(handler)
    api = ApiClient(base_url="http://api.test", transport=httpx.MockTransport(rec), backoff=0.0, **kw)
    return api, rec


def as_user():
    return principal_scope(USER)
