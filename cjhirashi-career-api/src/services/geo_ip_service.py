"""
Resolves a visitor IP to country/region/city via ipapi.co (free tier, no key
needed at this volume). Best-effort only: any failure (timeout, rate limit,
private/invalid IP) returns None and the caller just stores the event without
geo data - tracking must never break on a flaky third-party lookup.

Results are cached in-process by IP for the life of the worker (personal-site
traffic volume; no need for a shared/persistent cache). The raw IP itself is
only ever used as a lookup key here - routes/events.py never persists it.
"""
import ipaddress
import logging
from dataclasses import dataclass
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

_TIMEOUT = 3.0
_CACHE_MAX_SIZE = 5000

_geo_cache: dict[str, Optional["GeoInfo"]] = {}


@dataclass
class GeoInfo:
    country: Optional[str]
    region: Optional[str]
    city: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]


def _is_public_ip(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return not (addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved)


async def resolve_geo(ip: Optional[str]) -> Optional[GeoInfo]:
    if not ip or not _is_public_ip(ip):
        return None

    if ip in _geo_cache:
        return _geo_cache[ip]

    geo: Optional[GeoInfo] = None
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(f"https://ipapi.co/{ip}/json/")
            response.raise_for_status()
            data = response.json()
        if not data.get("error"):
            geo = GeoInfo(
                country=data.get("country_name"),
                region=data.get("region"),
                city=data.get("city"),
                latitude=data.get("latitude"),
                longitude=data.get("longitude"),
            )
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("geo_ip_service: lookup failed for IP (not logged): %s", exc)

    if len(_geo_cache) >= _CACHE_MAX_SIZE:
        _geo_cache.clear()
    _geo_cache[ip] = geo
    return geo
