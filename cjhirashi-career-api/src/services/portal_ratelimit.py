"""Límite de ritmo en memoria por clave (visitante o IP) para la ingesta pública.

Ventana deslizante de 60 s dentro de un solo proceso: frena ráfagas de un
cliente descontrolado sin añadir infraestructura. No es una defensa contra un
ataque distribuido; esa capa le corresponde a Cloudflare.
"""
import time
from collections import deque
from typing import Deque, Dict, Optional

WINDOW_SECONDS = 60.0
MAX_TRACKED_KEYS = 20_000


class SlidingWindowLimiter:
    def __init__(self, limit: int, window: float = WINDOW_SECONDS) -> None:
        self.limit = limit
        self.window = window
        self._hits: Dict[str, Deque[float]] = {}

    def allow(self, key: str, now: Optional[float] = None) -> bool:
        now = time.monotonic() if now is None else now
        if len(self._hits) > MAX_TRACKED_KEYS:
            self._prune(now)
        hits = self._hits.setdefault(key, deque())
        while hits and now - hits[0] > self.window:
            hits.popleft()
        if len(hits) >= self.limit:
            return False
        hits.append(now)
        return True

    def _prune(self, now: float) -> None:
        for key in [k for k, h in self._hits.items() if not h or now - h[-1] > self.window]:
            del self._hits[key]
