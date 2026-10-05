"""In-memory sliding-window rate limiter for a single Uvicorn worker."""

import time
from collections import deque
from collections.abc import Callable


class SlidingWindowRateLimiter:
    """Allow at most ``limit`` hits per key within ``window_seconds``.

    State lives in process memory, which matches the single-worker deployment. With
    several workers each process would count separately, so the effective limit grows.
    """

    def __init__(
        self,
        *,
        limit: int,
        window_seconds: float,
        max_keys: int = 10_000,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self.max_keys = max_keys
        self._clock = clock
        self._hits: dict[str, deque[float]] = {}

    def allow(self, key: str) -> bool:
        """Record a hit and report whether it is within the limit."""
        now = self._clock()
        cutoff = now - self.window_seconds
        hits = self._hits.get(key)
        if hits is None:
            if len(self._hits) >= self.max_keys:
                self._prune(cutoff)
            hits = self._hits[key] = deque()
        while hits and hits[0] <= cutoff:
            hits.popleft()
        if len(hits) >= self.limit:
            return False
        hits.append(now)
        return True

    def _prune(self, cutoff: float) -> None:
        # Drop idle keys so a flood of distinct addresses cannot grow memory forever.
        for key in [key for key, hits in self._hits.items() if not hits or hits[-1] <= cutoff]:
            del self._hits[key]
        if len(self._hits) >= self.max_keys:
            self._hits.clear()
