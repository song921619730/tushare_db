"""TushareClient unit tests (mock httpx).

Covers: error classification, rate limiting, retry, context manager.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tushare_db.core.errors import (
    TushareError,
    TushareRateLimitError,
    TushareAuthError,
    TushareBizError,
    TushareTransientError,
)


class TestErrorClassification:
    """B12: HTTP status code → error class mapping."""

    def test_429_rate_limit(self):
        """429 → TushareRateLimitError."""
        from tushare_db.core.tushare_client import TushareClient

        mock_resp = MagicMock()
        mock_resp.status_code = 429

        client = TushareClient(token="fake")
        with patch.object(client._client, "post", return_value=mock_resp):
            with pytest.raises(TushareRateLimitError):
                client._make_request("daily")

    def test_401_auth_error(self):
        """401 → TushareAuthError (no retry)."""
        from tushare_db.core.tushare_client import TushareClient

        mock_resp = MagicMock()
        mock_resp.status_code = 401

        client = TushareClient(token="fake")
        with patch.object(client._client, "post", return_value=mock_resp):
            with pytest.raises(TushareAuthError):
                client._make_request("daily")

    def test_403_auth_error(self):
        """403 → TushareAuthError."""
        from tushare_db.core.tushare_client import TushareClient

        mock_resp = MagicMock()
        mock_resp.status_code = 403

        client = TushareClient(token="fake")
        with patch.object(client._client, "post", return_value=mock_resp):
            with pytest.raises(TushareAuthError):
                client._make_request("daily")

    def test_404_biz_error(self):
        """404 → TushareBizError (interface not found)."""
        from tushare_db.core.tushare_client import TushareClient

        mock_resp = MagicMock()
        mock_resp.status_code = 404

        client = TushareClient(token="fake")
        with patch.object(client._client, "post", return_value=mock_resp):
            with pytest.raises(TushareBizError):
                client._make_request("nonexistent")

    def test_500_transient_error(self):
        """500 → TushareTransientError (retried)."""
        from tushare_db.core.tushare_client import TushareClient

        mock_resp = MagicMock()
        mock_resp.status_code = 500

        client = TushareClient(token="fake")
        with patch.object(client._client, "post", return_value=mock_resp):
            with pytest.raises(TushareTransientError):
                client._make_request("daily")

    def test_502_transient_error(self):
        """502 → TushareTransientError."""
        from tushare_db.core.tushare_client import TushareClient

        mock_resp = MagicMock()
        mock_resp.status_code = 502

        client = TushareClient(token="fake")
        with patch.object(client._client, "post", return_value=mock_resp):
            with pytest.raises(TushareTransientError):
                client._make_request("daily")

    def test_503_transient_error(self):
        """503 → TushareTransientError."""
        from tushare_db.core.tushare_client import TushareClient

        mock_resp = MagicMock()
        mock_resp.status_code = 503

        client = TushareClient(token="fake")
        with patch.object(client._client, "post", return_value=mock_resp):
            with pytest.raises(TushareTransientError):
                client._make_request("daily")

    def test_504_transient_error(self):
        """504 → TushareTransientError."""
        from tushare_db.core.tushare_client import TushareClient

        mock_resp = MagicMock()
        mock_resp.status_code = 504

        client = TushareClient(token="fake")
        with patch.object(client._client, "post", return_value=mock_resp):
            with pytest.raises(TushareTransientError):
                client._make_request("daily")

    def test_non_200_generic_error(self):
        """Other non-200 status → TushareError."""
        from tushare_db.core.tushare_client import TushareClient

        mock_resp = MagicMock()
        mock_resp.status_code = 418

        client = TushareClient(token="fake")
        with patch.object(client._client, "post", return_value=mock_resp):
            with pytest.raises(TushareError):
                client._make_request("daily")


class TestSuccessfulCall:
    """Successful API response handling."""

    def test_successful_response(self):
        from tushare_db.core.tushare_client import TushareClient

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "code": 0,
            "data": {
                "fields": ["ts_code", "trade_date", "close"],
                "items": [["000001.SZ", "20240101", 15.5]],
            },
        }

        client = TushareClient(token="fake")
        with patch.object(client._client, "post", return_value=mock_resp):
            result = client._make_request("daily")

        assert result["code"] == 0
        assert len(result["data"]["items"]) == 1

    def test_business_error_from_api(self):
        """code != 0 in JSON → TushareBizError."""
        from tushare_db.core.tushare_client import TushareClient

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"code": -1, "msg": "Invalid token"}

        client = TushareClient(token="fake")
        with patch.object(client._client, "post", return_value=mock_resp):
            with pytest.raises(TushareBizError, match="Invalid token"):
                client._make_request("daily")


class TestRateLimiterIntegration:
    """Rate limiter acquire + cooldown."""

    def test_rate_limiter_timeout(self):
        """Limiter returns False → TushareRateLimitError."""
        from tushare_db.core.tushare_client import TushareClient

        limiter = MagicMock()
        limiter.acquire.return_value = False

        client = TushareClient(token="fake", limiter=limiter)
        with pytest.raises(TushareRateLimitError):
            client.call("daily")

    def test_429_triggers_cooldown(self):
        """429 response → limiter.cooldown called."""
        from tushare_db.core.tushare_client import TushareClient

        mock_resp = MagicMock()
        mock_resp.status_code = 429

        limiter = MagicMock()
        limiter.acquire.return_value = True

        client = TushareClient(token="fake", limiter=limiter)
        with patch.object(client._client, "post", return_value=mock_resp):
            with pytest.raises(TushareRateLimitError):
                client.call("daily")

        limiter.cooldown.assert_called()


class TestContextManager:
    """TushareClient as context manager."""

    def test_enter_exit(self):
        from tushare_db.core.tushare_client import TushareClient

        client = TushareClient(token="fake")
        with patch.object(client._client, "close") as mock_close:
            with client as c:
                assert c is client
            mock_close.assert_called_once()

    def test_close(self):
        from tushare_db.core.tushare_client import TushareClient

        client = TushareClient(token="fake")
        with patch.object(client._client, "close") as mock_close:
            client.close()
            mock_close.assert_called_once()


class TestParamsHash:
    """TushareClient.params_hash utility."""

    def test_deterministic(self):
        from tushare_db.core.tushare_client import TushareClient

        params = {"ts_code": "000001.SZ", "start_date": "20240101"}
        h1 = TushareClient.params_hash(params)
        h2 = TushareClient.params_hash(params)
        assert h1 == h2

    def test_order_independent(self):
        """Same params in different order → same hash."""
        from tushare_db.core.tushare_client import TushareClient

        h1 = TushareClient.params_hash({"a": 1, "b": 2})
        h2 = TushareClient.params_hash({"b": 2, "a": 1})
        assert h1 == h2

    def test_different_params(self):
        from tushare_db.core.tushare_client import TushareClient

        h1 = TushareClient.params_hash({"ts_code": "000001.SZ"})
        h2 = TushareClient.params_hash({"ts_code": "600519.SH"})
        assert h1 != h2
