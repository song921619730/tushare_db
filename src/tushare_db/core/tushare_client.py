"""Tushare Pro API client using httpx with HTTP/2 multiplexing.

Features:
- httpx.Client(http2=True, timeout=10s) for 30% faster multi-call vs requests
- tenacity retry with exponential backoff for 429/500/502/503/504/timeout
- 429 triggers full-bucket cooldown (60s)
- 401/403/404 raise TushareAuthError or TushareBizError immediately (no retry)
- Connection recycling every 1500 requests to avoid HTTP/2 stream ID exhaustion
  (last_stream_id:1999 errors on long-running workers with special-bucket APIs)
"""

from __future__ import annotations

import hashlib
import json
import logging
import threading
import time
from typing import Any

import httpx
import structlog
from httpx import Limits, RemoteProtocolError, NetworkError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
    after_log,
)

from tushare_db.core.errors import TushareError, TushareRateLimitError, TushareAuthError, TushareBizError, TushareTransientError
from tushare_db.core.rate_limiter import DualRateLimiter

logger = structlog.get_logger()
_retry_logger = logging.getLogger("tushare.retry")


class TushareClient:
    """HTTP/2 client for Tushare Pro API with rate limiting and retry."""

    BASE_URL = "https://api.tushare.pro"

    # Recycle connections after this many requests to avoid HTTP/2 stream ID exhaustion.
    # HTTP/2 max stream ID is 2^31-1, but Tushare's server appears to cap at ~2000 per connection.
    _MAX_REQUESTS_PER_CONN = 1500

    def __init__(
        self,
        token: str,
        limiter: DualRateLimiter | None = None,
        timeout: float | httpx.Timeout = httpx.Timeout(connect=15, read=60, write=15, pool=10),
    ) -> None:
        self._token = token
        self._limiter = limiter or DualRateLimiter()
        self._timeout = timeout
        self._request_count = 0
        self._client = self._new_client()
        self._lock = threading.Lock()

    def _new_client(self) -> httpx.Client:
        return httpx.Client(
            http2=True,
            timeout=self._timeout,
            limits=Limits(max_connections=20, max_keepalive_connections=20),
        )

    def _maybe_recycle(self) -> None:
        """Close and recreate the httpx client to reset HTTP/2 stream ID counter."""
        with self._lock:
            self._request_count += 1
            if self._request_count >= self._MAX_REQUESTS_PER_CONN:
                try:
                    self._client.close()
                except Exception:
                    pass
                self._request_count = 0
                self._client = self._new_client()

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "TushareClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def _make_request(self, interface: str, **params: Any) -> dict[str, Any]:
        """Make a single API call to Tushare."""
        self._maybe_recycle()
        payload = {
            "api_name": interface,
            "token": self._token,
            "params": params,
        }
        try:
            resp = self._client.post(self.BASE_URL, json=payload)
        except (RemoteProtocolError, NetworkError) as e:
            raise TushareTransientError(f"Network error for {interface}: {e}") from e

        if resp.status_code == 429:
            raise TushareRateLimitError(f"Rate limit on {interface}")
        if resp.status_code in (401, 403):
            raise TushareAuthError(f"Auth failed for {interface}: {resp.status_code}")
        if resp.status_code == 404:
            raise TushareBizError(f"Interface not found: {interface}")
        if 500 <= resp.status_code < 600:
            raise TushareTransientError(f"Server error {resp.status_code} for {interface}")
        if resp.status_code != 200:
            raise TushareError(f"HTTP {resp.status_code} for {interface}")

        data = resp.json()
        if data.get("code") != 0:
            msg = data.get("msg", "Unknown error")
            raise TushareBizError(f"{interface}: {msg}")

        return data

    def call(
        self,
        interface: str,
        bucket: str = "normal",
        timeout: float = 120.0,
        **params: Any,
    ) -> dict[str, Any]:
        """Call Tushare API with rate limiting and retry.

        Args:
            interface: Tushare API name (e.g., 'daily', 'income').
            bucket: 'normal' or 'special' rate limit bucket.
            timeout: Max seconds to wait for rate limiter token (default 120s).
            **params: API parameters (e.g., ts_code='000001.SZ', start_date='20240101').

        Returns:
            Parsed API response with fields, data, etc.
        """
        # Acquire rate limiter token
        acquired = self._limiter.acquire(bucket, timeout)
        if not acquired:
            raise TushareRateLimitError(f"Rate limiter timeout for {interface}")

        start = time.monotonic()
        try:
            result = self._call_with_retry(interface, **params)
        except TushareRateLimitError:
            # 429: cool down the entire bucket
            self._limiter.cooldown(bucket)
            raise
        except TushareAuthError:
            # Don't retry auth errors
            raise
        except TushareBizError:
            # Don't retry business errors
            raise
        except TushareTransientError:
            # Transient errors are retried by tenacity; fall through to error handler if exhausted
            raise
        except TushareError as e:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            logger.error(
                "api_call_failed",
                interface=interface,
                status=0,
                duration_ms=elapsed_ms,
                error=str(e),
            )
            raise

        elapsed_ms = int((time.monotonic() - start) * 1000)
        rows = len(result.get("data", {}).get("items", []))

        logger.debug(
            "api_call_success",
            interface=interface,
            status=200,
            rows=rows,
            duration_ms=elapsed_ms,
        )

        return result

    @retry(
        retry=retry_if_exception_type((TushareRateLimitError, TushareTransientError)),
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        before_sleep=before_sleep_log(_retry_logger, logging.WARNING),
        after=after_log(_retry_logger, logging.INFO),
        reraise=True,
    )
    def _call_with_retry(self, interface: str, **params: Any) -> dict[str, Any]:
        """Internal method with tenacity retry decoration."""
        return self._make_request(interface, **params)

    @staticmethod
    def params_hash(params: dict[str, Any]) -> int:
        """Deterministic hash of API params for audit tracking."""
        key = json.dumps(params, sort_keys=True)
        return int(hashlib.md5(key.encode()).hexdigest()[:16], 16)
