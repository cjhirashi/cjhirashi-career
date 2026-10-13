"""Contexto de credencial del turno (RF-004).

Dos orígenes posibles de credencial hacia la API:
- `Principal`: el usuario autenticado de una petición HTTP; se reenvía SU JWT.
- `ServiceContext`: la cuenta de servicio (`AI_SERVICE_TOKEN`) para tareas programadas sin sesión.
  Se activa de forma explícita (`service_scope`), nunca por defecto.
Ambos viajan en `contextvars`, así las delegaciones y subtareas del turno heredan la credencial.
"""
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Iterator, Optional


@dataclass(frozen=True)
class Principal:
    user_id: str
    token: str = field(repr=False)


@dataclass(frozen=True)
class ServiceContext:
    token: str = field(repr=False)

    @classmethod
    def from_settings(cls) -> "ServiceContext":
        from config import settings

        return cls(token=settings.AI_SERVICE_TOKEN)


_principal: ContextVar[Optional[Principal]] = ContextVar("principal", default=None)
_service: ContextVar[Optional[ServiceContext]] = ContextVar("service_context", default=None)


def current_principal() -> Optional[Principal]:
    return _principal.get()


def current_service_context() -> Optional[ServiceContext]:
    return _service.get()


@contextmanager
def principal_scope(principal: Principal) -> Iterator[Principal]:
    token = _principal.set(principal)
    try:
        yield principal
    finally:
        _principal.reset(token)


@contextmanager
def service_scope(ctx: ServiceContext) -> Iterator[ServiceContext]:
    token = _service.set(ctx)
    try:
        yield ctx
    finally:
        _service.reset(token)
