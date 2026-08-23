"""In-process sliding-window rate limiting for authentication endpoints."""

import time
from collections import OrderedDict
from collections.abc import Callable


class SlidingWindowLimiter:
    """Bounded sliding-window failure tracker keyed by arbitrary strings."""

    def __init__(
        self,
        max_failures: int,
        window_seconds: int,
        clock: Callable[[], float] = time.monotonic,
        max_keys: int = 10_000,
    ) -> None:
        """Configure window size and memory bound."""
        assert max_failures >= 1, "max_failures must allow at least one attempt"
        assert window_seconds >= 1, "window_seconds must be positive"
        assert max_keys >= 1, "max_keys must be positive"
        self._max_failures = max_failures
        self._window_seconds = window_seconds
        self._clock = clock
        self._max_keys = max_keys
        # OrderedDict gives O(1) insertion-order eviction for bounded memory.
        self._failures: OrderedDict[str, list[float]] = OrderedDict()

    def _prune(self, key: str, now: float) -> None:
        """Drop expired failure timestamps for one key."""
        failures = self._failures.get(key)
        if failures is None:
            return
        cutoff = now - self._window_seconds
        while failures and failures[0] <= cutoff:
            assert len(failures) > 0
            failures.pop(0)
        if not failures:
            del self._failures[key]

    def check(self, key: str) -> tuple[bool, int]:
        """Return (blocked?, retry_after_seconds) without recording anything."""
        assert isinstance(key, str) and key
        now = self._clock()
        self._prune(key, now)

        failures = self._failures.get(key)
        if failures is None or len(failures) < self._max_failures:
            return False, 0

        oldest = failures[0]
        retry_after = max(1, int(self._window_seconds - (now - oldest)))
        return True, retry_after

    def record_failure(self, key: str) -> None:
        """Record a failed attempt, evicting the oldest key past the bound."""
        assert isinstance(key, str) and key
        now = self._clock()
        self._prune(key, now)

        if key not in self._failures and len(self._failures) >= self._max_keys:
            self._failures.popitem(last=False)

        self._failures.setdefault(key, []).append(now)

    def reset(self, key: str) -> None:
        """Clear tracked failures for one key."""
        assert isinstance(key, str) and key
        self._failures.pop(key, None)

    def reset_all(self) -> None:
        """Clear every tracked key (used by tests and admin tooling)."""
        self._failures.clear()


_LOGIN_LIMITER = SlidingWindowLimiter(max_failures=5, window_seconds=900)


def get_login_limiter() -> SlidingWindowLimiter:
    """Process-wide limiter enforcing T-203 (5 failures / 15 minutes / IP)."""
    return _LOGIN_LIMITER
