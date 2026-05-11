"""Custom exception types for the ingestion pipeline."""

from __future__ import annotations


class TushareError(Exception):
    """Base exception for Tushare API errors."""


class TushareRateLimitError(TushareError):
    """HTTP 429 rate limit exceeded."""


class TushareAuthError(TushareError):
    """Authentication failure (401/403)."""


class TushareBizError(TushareError):
    """Business logic error (Tushare returns 200 with error code)."""


class TushareTransientError(TushareError):
    """Transient error — safe to retry (5xx, network failures)."""


class SchemaInferenceError(Exception):
    """Failed to infer ClickHouse schema from sample data."""


class SinkError(Exception):
    """Failed to write data to ClickHouse."""
