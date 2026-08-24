"""Best-effort import of a single vacancy URL (LinkedIn/Indeed/OCC/…)."""
import re
from html import unescape
from typing import Optional
from urllib.parse import urlparse

from services.job_discovery.http import get_text
from services.job_discovery.types import JobListing

_HOST_SOURCE = (
    ("linkedin.com", "linkedin"),
    ("indeed.com", "indeed"),
    ("getonbrd.com", "getonboard"),
    ("getonboard.com", "getonboard"),
    ("occ.com.mx", "occ"),
    ("occ.com", "occ"),
    ("remotive.com", "remotive"),
    ("remoteok.com", "remoteok"),
    ("greenhouse.io", "greenhouse"),
    ("lever.co", "lever"),
    ("github.com", "github"),
)


# ============================================================================
# Inferencia de fuente
# ============================================================================

def infer_source(url: str) -> str:
    host = (urlparse(url).hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    for suffix, source in _HOST_SOURCE:
        if host == suffix or host.endswith("." + suffix):
            return source
    return "url"


# ============================================================================
# Extracción de metadatos HTML
# ============================================================================

def _meta(html: str, *keys: str) -> Optional[str]:
    for key in keys:
        pattern = (
            rf'<meta[^>]+(?:property|name)=["\']{re.escape(key)}["\'][^>]+content=["\']([^"\']+)["\']'
            rf'|<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\']{re.escape(key)}["\']'
        )
        match = re.search(pattern, html, flags=re.IGNORECASE)
        if match:
            value = unescape(match.group(1) or match.group(2) or "").strip()
            if value:
                return value
    return None


def _title_tag(html: str) -> Optional[str]:
    match = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    text = unescape(re.sub(r"\s+", " ", match.group(1))).strip()
    return text or None


def listing_from_html(url: str, html: str) -> JobListing:
    source = infer_source(url)
    title = _meta(html, "og:title", "twitter:title") or _title_tag(html)
    site = _meta(html, "og:site_name")
    description = _meta(html, "og:description", "description")
    company = site or source
    role = title or "Vacante importada"
    # Common "Role - Company | LinkedIn" split.
    if title and " - " in title:
        left, right = title.split(" - ", 1)
        if left.strip():
            role = left.strip()
        if right.strip() and company in (source, site):
            company = right.split("|")[0].strip() or company
    return JobListing(
        company=company[:255],
        exact_role=role[:255],
        vacancy_url=url[:500],
        source=source,
        snippet=(description or "")[:400] or None,
    )


# ============================================================================
# Importación de URL
# ============================================================================

async def import_url(url: str) -> JobListing:
    normalized = url.strip()
    if not normalized.startswith(("http://", "https://")):
        normalized = "https://" + normalized
    source = infer_source(normalized)
    try:
        status, html = await get_text(normalized)
        if status < 400 and html:
            return listing_from_html(normalized, html)
    except Exception:
        pass
    return JobListing(
        company=source if source != "url" else "Unknown",
        exact_role="Vacante importada",
        vacancy_url=normalized[:500],
        source=source,
        snippet="No se pudo leer el título de la página (el host suele bloquear bots). Completa empresa y rol al guardar.",
    )
