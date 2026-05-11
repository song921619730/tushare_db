"""Unit tests for incremental update module."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from tushare_db.runner.incremental import (
    get_latest_trade_date,
    get_target_date,
    filter_by_batch,
)
from tushare_db.config.models import InterfaceSpec, FetchStrategy


def _mock_result(rows):
    """Create a mock query result."""
    result = MagicMock()
    result.result_rows = rows
    return result


class TestGetLatestTradeDate:
    """Test get_latest_trade_date function."""

    def test_returns_most_recent_trading_date(self):
        """Should return the most recent trading date <= today."""
        mock_client = MagicMock()
        mock_client.query.return_value = _mock_result([(date(2026, 4, 24),)])

        result = get_latest_trade_date(mock_client)
        assert result == "20260424"

    def test_returns_none_when_no_trading_dates(self):
        """Should return None if trade_cal is empty."""
        mock_client = MagicMock()
        mock_client.query.return_value = _mock_result([])

        result = get_latest_trade_date(mock_client)
        assert result is None

    def test_filters_future_dates(self):
        """Should not return dates after today."""
        mock_client = MagicMock()
        mock_client.query.return_value = _mock_result([])

        # Verify the query includes a date filter
        get_latest_trade_date(mock_client)
        call_args = mock_client.query.call_args[0][0]
        assert "<=" in call_args  # Should filter for dates <= today


class TestGetTargetDate:
    """Test get_target_date function."""

    def test_returns_trading_date_before_latest(self):
        """Should return the trading date before the latest one."""
        mock_client = MagicMock()
        # First call: latest date
        # Second call: previous date
        mock_client.query.side_effect = [
            _mock_result([(date(2026, 4, 24),)]),
            _mock_result([(date(2026, 4, 23),)]),
        ]

        result = get_target_date(mock_client)
        assert result == "20260423"

    def test_returns_none_when_no_previous_date(self):
        """Should return None if there's no previous trading date."""
        mock_client = MagicMock()
        mock_client.query.side_effect = [
            _mock_result([(date(2026, 4, 24),)]),
            _mock_result([]),
        ]

        result = get_target_date(mock_client)
        assert result is None


class TestFilterByBatch:
    """Test filter_by_batch function."""

    def _make_spec(self, name: str, batch: str) -> InterfaceSpec:
        """Create a minimal InterfaceSpec."""
        return InterfaceSpec(
            name=name,
            table=f"tushare_{name}",
            enabled=True,
            priority="P0",
            mode="incremental",
            freq_bucket="normal",
            fetch_strategy=FetchStrategy(kind="date_loop"),
            order_by="ts_code, trade_date",
            batch=batch,
        )

    def test_filters_by_batch(self):
        """Should only return specs matching the given batch."""
        specs = [
            self._make_spec("daily", "A"),
            self._make_spec("moneyflow", "B"),
            self._make_spec("daily_basic", "A"),
        ]

        result = filter_by_batch(specs, "A")
        assert len(result) == 2
        assert {s.name for s in result} == {"daily", "daily_basic"}

    def test_returns_empty_when_no_match(self):
        """Should return empty list when no specs match the batch."""
        specs = [
            self._make_spec("daily", "A"),
            self._make_spec("moneyflow", "B"),
        ]

        result = filter_by_batch(specs, "D")
        assert result == []
