"""Dual token-bucket rate limiter with sliding window.

Two independent buckets:
- NORMAL_BUCKET: 475/min (95% of 500)
- SPECIAL_BUCKET: 285/min (95% of 300)

Implementation: collections.deque + threading.Lock sliding window (ms precision).
Buckets are independent and non-blocking — a slow normal bucket doesn't stall the special one.
"""

from __future__ import annotations

import time
import threading
from collections import deque

from tushare_db.core.clock import Clock, SystemClock


class TokenBucket:
    """Sliding-window rate limiter for a single bucket.

    Args:
        rpm: Maximum requests per minute.
        clock: Time source (injected for testing).
    """

    def __init__(self, rpm: int, clock: Clock | None = None) -> None:
        self._rpm = rpm
        self._window_sec = 60.0
        self._timestamps: deque[float] = deque()
        self._lock = threading.Lock()
        self._clock = clock or SystemClock()

    @property
    def rpm(self) -> int:
        return self._rpm

    def acquire(self, timeout: float = 30.0) -> bool:
        """Block until a token is available or timeout expires.

        Returns True if token was acquired, False on timeout.
        """
        deadline = time.monotonic() + timeout
        while True:
            with self._lock:
                self._evict_expired()
                if len(self._timestamps) < self._rpm:
                    self._timestamps.append(time.monotonic())
                    return True
                # Calculate wait until oldest timestamp expires
                wait = self._timestamps[0] + self._window_sec - time.monotonic()

            wait = min(max(wait, 0.01), deadline - time.monotonic())
            if wait <= 0:
                return False
            time.sleep(wait)

    def _evict_expired(self) -> None:
        """Remove timestamps older than the sliding window."""
        cutoff = time.monotonic() - self._window_sec
        while self._timestamps and self._timestamps[0] < cutoff:
            self._timestamps.popleft()

    @property
    def current_count(self) -> int:
        with self._lock:
            self._evict_expired()
            return len(self._timestamps)

    @property
    def utilization(self) -> float:
        with self._lock:
            self._evict_expired()
            return len(self._timestamps) / self._rpm if self._rpm > 0 else 0.0


class DualRateLimiter:
    """Manages normal and special buckets independently.

    Callers specify which bucket to use when acquiring a token.
    """

    def __init__(
        self,
        normal_rpm: int = 475,
        special_rpm: int = 285,
        clock: Clock | None = None,
    ) -> None:
        self.normal = TokenBucket(normal_rpm, clock)
        self.special = TokenBucket(special_rpm, clock)

    def acquire(self, bucket: str = "normal", timeout: float = 30.0) -> bool:
        """Acquire a token from the specified bucket."""
        if bucket == "special":
            return self.special.acquire(timeout)
        return self.normal.acquire(timeout)

    def cooldown(self, bucket: str = "normal") -> None:
        """Cool down an entire bucket (e.g., after 429 response).

        Fills the token bucket to capacity so acquire() must wait for
        the full sliding window before allowing new requests.
        """
        target = self.special if bucket == "special" else self.normal
        with target._lock:
            now = time.monotonic()
            target._timestamps.clear()
            # Fill the bucket so acquire() must wait for window expiry
            target._timestamps.extend([now] * target._rpm)
