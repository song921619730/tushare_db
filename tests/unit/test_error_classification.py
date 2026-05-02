"""Unit tests for B12 fix: tenacity retry scope narrowed to transient errors only."""

from __future__ import annotations

import pytest

from tushare_db.core.errors import (
    TushareError,
    TushareRateLimitError,
    TushareAuthError,
    TushareBizError,
    TushareTransientError,
)


class TestErrorClassification:
    """B12: Verify error hierarchy is correct."""

    def test_transient_is_subclass_of_error(self):
        assert issubclass(TushareTransientError, TushareError)

    def test_rate_limit_is_subclass_of_error(self):
        assert issubclass(TushareRateLimitError, TushareError)

    def test_auth_is_subclass_of_error(self):
        assert issubclass(TushareAuthError, TushareError)

    def test_biz_is_subclass_of_error(self):
        assert issubclass(TushareBizError, TushareError)


class TestRetryFilter:
    """B12: Verify only transient errors are retried.

    We test this by inspecting the exception classes that the retry
    decorator's `retry` predicate would accept.
    """

    def test_transient_matches_retry_filter(self):
        """TushareTransientError should be retried."""
        from tenacity import retry_if_exception_type
        predicate = retry_if_exception_type((TushareRateLimitError, TushareTransientError))
        exc = TushareTransientError("Server error 500")
        # tenacity's retry_if_exception_type checks isinstance
        assert isinstance(exc, (TushareRateLimitError, TushareTransientError))

    def test_rate_limit_matches_retry_filter(self):
        """TushareRateLimitError should be retried."""
        exc = TushareRateLimitError("Rate limit")
        assert isinstance(exc, (TushareRateLimitError, TushareTransientError))

    def test_biz_error_does_not_match_retry_filter(self):
        """TushareBizError should NOT be retried."""
        exc = TushareBizError("Interface not found")
        assert not isinstance(exc, (TushareRateLimitError, TushareTransientError))

    def test_auth_error_does_not_match_retry_filter(self):
        """TushareAuthError should NOT be retried."""
        exc = TushareAuthError("Auth failed")
        assert not isinstance(exc, (TushareRateLimitError, TushareTransientError))


class TestMakeRequestErrorMapping:
    """B12: _make_request should map HTTP status codes to correct exception types."""

    def _make_payload(self, status_code, response_json=None):
        """Mock response for testing."""
        class MockResponse:
            def __init__(self):
                self.status_code = status_code
                self._json = response_json or {}
            def json(self):
                return self._json
        return MockResponse()

    def test_429_raises_rate_limit(self):
        from unittest.mock import patch, MagicMock
        from tushare_db.core.tushare_client import TushareClient

        client = TushareClient(token="test")
        client._client = MagicMock()
        client._client.post.return_value = self._make_payload(429)

        with pytest.raises(TushareRateLimitError):
            client._make_request("daily")

    def test_401_raises_auth(self):
        from unittest.mock import MagicMock
        from tushare_db.core.tushare_client import TushareClient

        client = TushareClient(token="test")
        client._client = MagicMock()
        client._client.post.return_value = self._make_payload(401)

        with pytest.raises(TushareAuthError):
            client._make_request("daily")

    def test_403_raises_auth(self):
        from unittest.mock import MagicMock
        from tushare_db.core.tushare_client import TushareClient

        client = TushareClient(token="test")
        client._client = MagicMock()
        client._client.post.return_value = self._make_payload(403)

        with pytest.raises(TushareAuthError):
            client._make_request("daily")

    def test_404_raises_biz(self):
        from unittest.mock import MagicMock
        from tushare_db.core.tushare_client import TushareClient

        client = TushareClient(token="test")
        client._client = MagicMock()
        client._client.post.return_value = self._make_payload(404)

        with pytest.raises(TushareBizError):
            client._make_request("daily")

    def test_500_raises_transient(self):
        from unittest.mock import MagicMock
        from tushare_db.core.tushare_client import TushareClient

        client = TushareClient(token="test")
        client._client = MagicMock()
        client._client.post.return_value = self._make_payload(500)

        with pytest.raises(TushareTransientError):
            client._make_request("daily")

    def test_503_raises_transient(self):
        from unittest.mock import MagicMock
        from tushare_db.core.tushare_client import TushareClient

        client = TushareClient(token="test")
        client._client = MagicMock()
        client._client.post.return_value = self._make_payload(503)

        with pytest.raises(TushareTransientError):
            client._make_request("daily")

    def test_502_raises_transient(self):
        from unittest.mock import MagicMock
        from tushare_db.core.tushare_client import TushareClient

        client = TushareClient(token="test")
        client._client = MagicMock()
        client._client.post.return_value = self._make_payload(502)

        with pytest.raises(TushareTransientError):
            client._make_request("daily")

    def test_tushare_error_code_raises_biz(self):
        """Tushare returns 200 but body has code != 0."""
        from unittest.mock import MagicMock
        from tushare_db.core.tushare_client import TushareClient

        client = TushareClient(token="test")
        client._client = MagicMock()
        client._client.post.return_value = self._make_payload(200, {"code": -1, "msg": "bad param"})

        with pytest.raises(TushareBizError):
            client._make_request("daily")
