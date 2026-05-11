"""Rate limiter concurrent test: 10 workers racing for tokens,
assert total calls in 60 seconds <= bucket capacity.
"""

from __future__ import annotations

import threading
import time

import pytest

from tushare_db.core.rate_limiter import TokenBucket, DualRateLimiter


class TestRateLimiterConcurrent:
    """Test rate limiter under concurrent access."""

    def test_token_bucket_concurrent_calls(self):
        """10 workers racing for tokens — total calls in 60s <= rpm."""
        rpm = 100  # 100 requests per minute
        bucket = TokenBucket(rpm=rpm)
        call_count = 0
        lock = threading.Lock()
        barrier = threading.Barrier(10)

        def worker():
            nonlocal call_count
            barrier.wait()  # Synchronize start
            local_count = 0
            deadline = time.monotonic() + 60.0
            while time.monotonic() < deadline:
                if bucket.acquire(timeout=0.1):
                    local_count += 1
                else:
                    break  # Timeout — stop trying
            with lock:
                call_count += local_count

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=120)

        # Total calls should not exceed the bucket capacity
        assert call_count <= rpm, (
            f"Rate limiter failed: {call_count} calls exceeded {rpm} rpm "
            f"across 10 concurrent workers"
        )

    def test_dual_rate_limiter_independent_buckets(self):
        """Normal and special buckets are independent."""
        limiter = DualRateLimiter(normal_rpm=100, special_rpm=50)

        # Fill normal bucket
        normal_count = 0
        deadline = time.monotonic() + 60.0
        while time.monotonic() < deadline:
            if limiter.acquire("normal", timeout=0.1):
                normal_count += 1
            else:
                break

        # Fill special bucket
        special_count = 0
        deadline = time.monotonic() + 60.0
        while time.monotonic() < deadline:
            if limiter.acquire("special", timeout=0.1):
                special_count += 1
            else:
                break

        assert normal_count <= 100
        assert special_count <= 50

    def test_cooldown_blocks_requests(self):
        """After cooldown, acquire should wait for full window."""
        bucket = TokenBucket(rpm=10)
        # Use some tokens
        for _ in range(5):
            bucket.acquire()

        # Cooldown should fill bucket
        bucket._timestamps.clear()
        now = time.monotonic()
        with bucket._lock:
            bucket._timestamps.extend([now] * bucket._rpm)

        # Next acquire should timeout (bucket is full)
        start = time.monotonic()
        acquired = bucket.acquire(timeout=0.5)
        elapsed = time.monotonic() - start

        assert not acquired, "Cooldown should block acquire"
        assert elapsed >= 0.4, "Cooldown should wait close to timeout duration"


class TestTokenBucket:
    """Test individual TokenBucket behavior."""

    def test_basic_acquire(self):
        """Single acquire should succeed immediately."""
        bucket = TokenBucket(rpm=60)
        assert bucket.acquire() is True

    def test_evict_expired(self):
        """Old timestamps should be evicted."""
        bucket = TokenBucket(rpm=60)
        # Manually add old timestamps
        with bucket._lock:
            old_time = time.monotonic() - 120  # 2 minutes ago
            bucket._timestamps.extend([old_time] * 50)
        assert len(bucket._timestamps) == 50

        bucket._evict_expired()
        assert len(bucket._timestamps) == 0

    def test_current_count(self):
        """current_count should reflect active window."""
        bucket = TokenBucket(rpm=60)
        bucket.acquire()
        bucket.acquire()
        assert bucket.current_count == 2

    def test_utilization(self):
        """utilization should be between 0 and 1."""
        bucket = TokenBucket(rpm=60)
        assert bucket.utilization == 0.0

        bucket.acquire()
        assert 0.0 < bucket.utilization <= 1.0

    def test_timeout_returns_false(self):
        """When bucket is full, acquire with short timeout should fail."""
        bucket = TokenBucket(rpm=2)
        bucket.acquire()
        bucket.acquire()

        # Bucket is full, wait should return False
        assert bucket.acquire(timeout=0.1) is False
