"""In-memory preview of the last discovery, keyed by user + session.

Carlos authorizes by ref (L1, L2…). The agent must not persist vacancies
that were not in this preview. HTTP Admin searches also fill the `last`
bucket so the sidebar chat can save the same results.
"""
from __future__ import annotations

import re
import threading
import time
from typing import Dict, Iterable, List, Optional, Tuple

_TTL_SECONDS = 2 * 60 * 60
_LOCK = threading.Lock()
_STORE: Dict[Tuple[int, str], tuple[float, Dict[str, dict]]] = {}
LAST_KEY = "last"

_REF_RE = re.compile(r"^(?:L)?(\d+)$", re.IGNORECASE)


# ============================================================================
# Normalización de referencias
# ============================================================================

def normalize_ref(raw: str) -> Optional[str]:
    text = (raw or "").strip().upper()
    match = _REF_RE.match(text)
    if not match:
        return None
    return f"L{int(match.group(1))}"


def _purge_locked(now: float) -> None:
    expired = [key for key, (expires_at, _) in _STORE.items() if expires_at <= now]
    for key in expired:
        del _STORE[key]


def _write(user_id: str, session_key: str, listings: Dict[str, dict]) -> None:
    now = time.time()
    _purge_locked(now)
    _STORE[(user_id, session_key or "admin")] = (now + _TTL_SECONDS, listings)


# ============================================================================
# Almacenamiento de preview
# ============================================================================

def remember_preview(user_id: str, session_key: str, listings: List[dict]) -> List[dict]:
    """Replace the preview, assign L1..Ln, and mirror to `last`."""
    indexed: Dict[str, dict] = {}
    out: List[dict] = []
    for index, raw in enumerate(listings, start=1):
        ref = f"L{index}"
        item = dict(raw)
        item["ref"] = ref
        indexed[ref] = item
        out.append(item)
    with _LOCK:
        _write(user_id, session_key or "admin", indexed)
        if (session_key or "admin") != LAST_KEY:
            _write(user_id, LAST_KEY, indexed)
    return out


def append_preview(user_id: str, session_key: str, listing: dict) -> dict:
    """Append one listing as the next Ln on the session and `last` buckets."""
    item = dict(listing)
    with _LOCK:
        now = time.time()
        _purge_locked(now)
        key = (user_id, session_key or "admin")
        _expires, current = _STORE.get(key, (now + _TTL_SECONDS, {}))
        current = dict(current)
        next_n = 1
        for ref in current:
            next_n = max(next_n, int(ref[1:]) + 1)
        ref = f"L{next_n}"
        item["ref"] = ref
        current[ref] = item
        _write(user_id, session_key or "admin", current)
        last_key = (user_id, LAST_KEY)
        _last_expires, last = _STORE.get(last_key, (now + _TTL_SECONDS, {}))
        last = dict(last)
        last[ref] = item
        _write(user_id, LAST_KEY, last)
    return item


# ============================================================================
# Resolución de referencias
# ============================================================================

def resolve_refs(
    user_id: str,
    session_key: str,
    refs: Iterable[str],
) -> tuple[List[dict], List[str], List[str]]:
    """Return (found, missing, available). Looks in the session bucket, then `last`."""
    wanted: List[str] = []
    missing: List[str] = []
    seen: set[str] = set()
    for raw in refs:
        ref = normalize_ref(str(raw))
        if not ref:
            missing.append(str(raw))
            continue
        if ref in seen:
            continue
        seen.add(ref)
        wanted.append(ref)

    with _LOCK:
        now = time.time()
        _purge_locked(now)
        bucket = _STORE.get((user_id, session_key or "admin"))
        if bucket is None or bucket[0] <= now:
            bucket = _STORE.get((user_id, LAST_KEY))
        indexed = dict(bucket[1]) if bucket and bucket[0] > now else {}

    found: List[dict] = []
    for ref in wanted:
        if ref in indexed:
            found.append(dict(indexed[ref]))
        else:
            missing.append(ref)
    available = sorted(indexed.keys(), key=lambda item: int(item[1:]))
    return found, missing, available


def reset_for_tests() -> None:
    with _LOCK:
        _STORE.clear()
