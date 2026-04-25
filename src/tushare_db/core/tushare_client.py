"""Tushare Pro API client using httpx with HTTP/2 multiplexing.

Features:
- httpx.Client(http2=True, timeout=10s) for 30% faster multi-call vs requests
- tenacity retry with exponential backoff for 429/500/502/503/504/timeout
- 429 triggers full-bucket cooldown (60s)
- 401/403/404 raise TushareAuthError or TushareBizError immediately (no retry)
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from typing import Any

import httpx
import structlog
from httpx import Limits
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

    def __init__(
        self,
        token: str,
        limiter: DualRateLimiter | None = None,
        timeout: float = 10.0,
    ) -> None:
        self._token = token
        self._limiter = limiter or DualRateLimiter()
        self._timeout = timeout
        self._client = httpx.Client(
            http2=True,
            timeout=httpx.Timeout(timeout),
            limits=Limits(max_connections=20, max_keepalive_connections=20),
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "TushareClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def _make_request(self, interface: str, **params: Any) -> dict[str, Any]:
        """Make a single API call to Tushare."""
        payload = {
            "api_name": interface,
            "token": self._token,
            "params": params,
        }
        resp = self._client.post(self.BASE_URL, json=payload)

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
        timeout: float = 30.0,
        **params: Any,
    ) -> dict[str, Any]:
        """Call Tushare API with rate limiting and retry.

        Args:
            interface: Tushare API name (e.g., 'daily', 'income').
            bucket: 'normal' or 'special' rate limit bucket.
            timeout: Max seconds to wait for rate limiter token.
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
