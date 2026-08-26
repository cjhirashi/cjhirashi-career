"""Shared httpx client for job-discovery adapters."""
from typing import Any, Mapping, Optional

import httpx

from config import settings


class JobDiscoveryHttpError(Exception):
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


# ============================================================================
# Cliente HTTP compartido
# ============================================================================

def _headers(extra: Optional[Mapping[str, str]] = None) -> dict[str, str]:
    headers = {
        "User-Agent": settings.JOB_DISCOVERY_USER_AGENT,
        "Accept": "application/json, text/html;q=0.8",
    }
    if extra:
        headers.update(extra)
    return headers


async def get_json(
    url: str,
    *,
    params: Optional[Mapping[str, Any]] = None,
    extra_headers: Optional[Mapping[str, str]] = None,
) -> Any:
    timeout = settings.JOB_DISCOVERY_TIMEOUT_SECONDS
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        response = await client.get(url, params=params, headers=_headers(extra_headers))
    if response.status_code >= 400:
        raise JobDiscoveryHttpError(
            f"{url} responded {response.status_code}",
            status_code=response.status_code,
        )
    return response.json()


async def get_text(
    url: str,
    *,
    extra_headers: Optional[Mapping[str, str]] = None,
) -> tuple[int, str]:
    timeout = settings.JOB_DISCOVERY_TIMEOUT_SECONDS
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        response = await client.get(url, headers=_headers(extra_headers))
    return response.status_code, response.text
