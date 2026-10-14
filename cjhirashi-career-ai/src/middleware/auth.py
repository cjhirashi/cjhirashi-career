"""Autenticación JWT del harness (RF-002, RF-019; contrato auth-jwt-service-account §2).

Valida el mismo `Authorization: Bearer <access_token>` que emite la API (SECRET_KEY + ALGORITHM
compartidos). No consulta la BD de usuarios ni llama a la API (riesgo R6 aceptado).

- 401 (sin procesar la petición): sin header, esquema distinto de Bearer, firma inválida, expirado,
  `exp` o `sub` ausentes, `type` distinto de `access` (ausente = `access`, D-27), `role` desconocido.
- 403: `role` agent o service (D-14: no usan chat ni gestión).
- Sin claim `role` = `user` (compatibilidad con tokens previos).
- Éxito: `Principal(user_id, token)` queda en `principal_scope` durante toda la request.

Formato de error: el de la API (`{"detail": str}` + `WWW-Authenticate: Bearer` en 401); el AI no
define otro. Los mensajes nunca incluyen texto del token.
"""
from typing import AsyncIterator

import jwt
from fastapi import HTTPException, Request, status

from config import settings
from middleware.principal import Principal, principal_scope

_USER_ROLES = frozenset({"user"})
_FORBIDDEN_ROLES = frozenset({"agent", "service"})


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _extract_bearer(request: Request) -> str:
    header = request.headers.get("Authorization")
    if not header:
        raise _unauthorized("Not authenticated")
    scheme, _, token = header.partition(" ")
    token = token.strip()
    if scheme.lower() != "bearer" or not token:
        raise _unauthorized("Not authenticated")
    return token


def authenticate_token(token: str) -> Principal:
    """Valida un access token de la API y devuelve el `Principal`. Lanza HTTPException 401/403."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"require": ["exp", "sub"]},  # D-27: sin `exp` o sin `sub` -> 401
        )
    except jwt.ExpiredSignatureError:
        raise _unauthorized("Token has expired") from None
    except jwt.InvalidTokenError:
        raise _unauthorized("Invalid token") from None

    # D-27: lista blanca. Ausente = access (tokens previos al despliegue); cualquier otro valor
    # (`refresh`, `linkedin_oauth_state`, ...) no es un access token.
    if payload.get("type", "access") != "access":
        raise _unauthorized("Invalid token type")

    user_id = payload.get("sub")
    if not isinstance(user_id, str) or not user_id:
        raise _unauthorized("Token inválido: falta información de usuario")

    role = payload.get("role", "user")
    if isinstance(role, str) and role in _FORBIDDEN_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Agent and service tokens are not authorized for this endpoint",
        )
    if not isinstance(role, str) or role not in _USER_ROLES:
        raise _unauthorized("Invalid token role")

    return Principal(user_id=user_id, token=token)


async def require_principal(request: Request) -> AsyncIterator[Principal]:
    """Dependencia FastAPI: autentica y mantiene `principal_scope` mientras dura la request."""
    principal = authenticate_token(_extract_bearer(request))
    with principal_scope(principal):
        yield principal
