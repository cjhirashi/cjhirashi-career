"""
Consulta web para el L3 agent_web_search.

Dos operaciones:
- `search`: Brave Search si hay API key; si no, DuckDuckGo HTML.
- `fetch`: GET de una URL pública, HTML reducido a texto.

SSRF: solo http/https, DNS a IP pública, redirects revalidados. No toca
PostgreSQL ni GitHub.
"""
from __future__ import annotations

import ipaddress
import logging
import re
import socket
from html.parser import HTMLParser
from typing import Any, Optional
from urllib.parse import parse_qs, unquote, urljoin, urlparse

import httpx

from config import settings

logger = logging.getLogger(__name__)

_USER_AGENT = "Portafolio-cjhirashi/1.0 (web-search; +https://cjhirashi.com)"
_MAX_RESULTS = 8
_MAX_TEXT_CHARS = 12_000
_MAX_FETCH_BYTES = 120_000
_TIMEOUT = 12.0
_MAX_REDIRECTS = 3
_BLOCKED_HOSTS = frozenset(
    {
        "localhost",
        "localhost.localdomain",
        "metadata.google.internal",
        "metadata.google.com",
        "169.254.169.254",
    }
)
_TAG_RE = re.compile(r"<[^>]+>")
_DDG_RESULT_RE = re.compile(
    r'class="result__a"[^>]*href="(?P<href>[^"]+)"[^>]*>(?P<title>.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)
_DDG_SNIPPET_RE = re.compile(
    r'class="result__snippet"[^>]*>(?P<snippet>.*?)</(?:a|td|span)',
    re.IGNORECASE | re.DOTALL,
)


class WebSearchError(Exception):
    pass


class _HtmlTextExtractor(HTMLParser):
    _skip_tags = frozenset({"script", "style", "noscript", "svg"})

    def __init__(self) -> None:
        super().__init__()
        self._skip = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        if tag in self._skip_tags:
            self._skip += 1
        if tag in {"p", "div", "br", "li", "h1", "h2", "h3", "tr"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in self._skip_tags and self._skip:
            self._skip -= 1

    def handle_data(self, data: str) -> None:
        if self._skip:
            return
        text = " ".join(data.split())
        if text:
            self.parts.append(text)


def html_to_text(html: str) -> str:
    parser = _HtmlTextExtractor()
    parser.feed(html or "")
    return re.sub(r"\n{3,}", "\n\n", " ".join(parser.parts)).strip()


def _strip_tags(html: str) -> str:
    return " ".join(_TAG_RE.sub(" ", html or "").split())


def unwrap_ddg_href(href: str) -> str:
    raw = href.strip()
    if raw.startswith("//"):
        raw = "https:" + raw
    parsed = urlparse(raw)
    uddg = parse_qs(parsed.query).get("uddg")
    if uddg:
        return unquote(uddg[0])
    return raw


def parse_ddg_html(html: str, limit: int) -> list[dict[str, str]]:
    titles = list(_DDG_RESULT_RE.finditer(html or ""))
    snippets = [_strip_tags(m.group("snippet")) for m in _DDG_SNIPPET_RE.finditer(html or "")]
    items: list[dict[str, str]] = []
    for i, match in enumerate(titles[:limit]):
        url = unwrap_ddg_href(match.group("href"))
        if not url.startswith("http"):
            continue
        items.append(
            {
                "title": _strip_tags(match.group("title")),
                "url": url,
                "snippet": snippets[i] if i < len(snippets) else "",
            }
        )
    return items


def parse_brave_payload(payload: dict[str, Any], limit: int) -> list[dict[str, str]]:
    rows = ((payload or {}).get("web") or {}).get("results") or []
    items: list[dict[str, str]] = []
    for row in rows[:limit]:
        url = (row.get("url") or "").strip()
        if not url.startswith("http"):
            continue
        items.append(
            {
                "title": (row.get("title") or "").strip(),
                "url": url,
                "snippet": (row.get("description") or "").strip(),
            }
        )
    return items


def _blocked_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped
    return bool(
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def assert_public_http_url(url: str) -> str:
    """Valida esquema, host y resolución DNS. Lanza WebSearchError si no es pública."""
    parsed = urlparse((url or "").strip())
    if parsed.scheme not in ("http", "https"):
        raise WebSearchError("Solo se permiten URLs http o https")
    host = (parsed.hostname or "").strip().lower().rstrip(".")
    if not host or host in _BLOCKED_HOSTS or host.endswith(".localhost"):
        raise WebSearchError("Host no permitido")
    if parsed.username or parsed.password:
        raise WebSearchError("URLs con credenciales no están permitidas")
    try:
        infos = socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise WebSearchError(f"No se pudo resolver el host: {host}") from exc
    if not infos:
        raise WebSearchError(f"No se pudo resolver el host: {host}")
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if _blocked_ip(ip):
            raise WebSearchError("La URL apunta a una red privada o reservada")
    return parsed.geturl()


def _headers() -> dict[str, str]:
    return {"User-Agent": _USER_AGENT, "Accept": "text/html,application/json;q=0.9,text/plain;q=0.8"}


async def _brave_search(query: str, limit: int) -> list[dict[str, str]]:
    key = (settings.BRAVE_SEARCH_API_KEY or "").strip()
    if not key:
        return []
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        response = await client.get(
            "https://api.search.brave.com/res/v1/web/search",
            params={"q": query, "count": limit},
            headers={"Accept": "application/json", "X-Subscription-Token": key, "User-Agent": _USER_AGENT},
        )
    if response.status_code >= 400:
        logger.warning("Brave search failed: %s %s", response.status_code, response.text[:200])
        raise WebSearchError(f"Brave Search respondió {response.status_code}")
    return parse_brave_payload(response.json(), limit)


async def _ddg_search(query: str, limit: int) -> list[dict[str, str]]:
    async with httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True) as client:
        response = await client.post(
            "https://html.duckduckgo.com/html/",
            data={"q": query},
            headers=_headers(),
        )
    if response.status_code >= 400:
        raise WebSearchError(f"DuckDuckGo respondió {response.status_code}")
    return parse_ddg_html(response.text, limit)


async def search(query: str, max_results: int = _MAX_RESULTS) -> dict[str, Any]:
    q = (query or "").strip()
    if not q:
        return {"error": "query required"}
    limit = max(1, min(int(max_results or _MAX_RESULTS), 10))
    provider = "brave" if (settings.BRAVE_SEARCH_API_KEY or "").strip() else "duckduckgo"
    try:
        items = await (_brave_search(q, limit) if provider == "brave" else _ddg_search(q, limit))
    except (WebSearchError, httpx.HTTPError) as exc:
        if provider == "brave":
            logger.info("Brave failed, falling back to DuckDuckGo: %s", exc)
            provider = "duckduckgo"
            try:
                items = await _ddg_search(q, limit)
            except (WebSearchError, httpx.HTTPError) as nested:
                return {"error": str(nested), "query": q}
        else:
            return {"error": str(exc), "query": q}
    return {"query": q, "provider": provider, "results": items}


async def fetch(url: str) -> dict[str, Any]:
    current = assert_public_http_url(url)
    async with httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=False) as client:
        for _ in range(_MAX_REDIRECTS + 1):
            try:
                response = await client.get(current, headers=_headers())
            except httpx.HTTPError as exc:
                return {"error": f"No se pudo leer la URL: {exc}"}
            if response.status_code in {301, 302, 303, 307, 308}:
                location = response.headers.get("location")
                if not location:
                    return {"error": "Redirect sin Location"}
                current = assert_public_http_url(urljoin(current, location))
                continue
            if response.status_code >= 400:
                return {"error": f"La página respondió {response.status_code}", "url": current}
            content_type = (response.headers.get("content-type") or "").split(";")[0].strip().lower()
            if content_type.startswith(("image/", "audio/", "video/", "application/pdf", "application/octet-stream")):
                return {"error": f"Tipo de contenido no textual: {content_type}", "url": current}
            raw = response.content[:_MAX_FETCH_BYTES]
            text = raw.decode(response.encoding or "utf-8", errors="replace")
            if "html" in content_type or text.lstrip()[:15].lower().startswith("<!doctype") or text.lstrip()[:6].lower().startswith("<html"):
                text = html_to_text(text)
            if len(text) > _MAX_TEXT_CHARS:
                text = text[:_MAX_TEXT_CHARS] + "…"
            return {"url": str(response.url), "content_type": content_type, "text": text}
    return {"error": "Demasiados redirects", "url": current}
