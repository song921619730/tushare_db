"""Unit tests for B8 fix: scheduler trade_cal pre-flight check."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch


class TestSchedulerPreflight:
    """B8: Verify scheduler exits if trade_cal is empty."""

    def test_start_scheduler_exits_if_trade_cal_empty(self):
        """If trade_cal has 0 rows, start_scheduler should raise SystemExit(2)."""
        from tushare_db.scheduler.service import start_scheduler

        # Mock the ClickHouse client
        mock_client = MagicMock()
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, idx: 0
        mock_client.query.return_value.result_rows = [mock_row]

        with patch("tushare_db.scheduler.jobs._get_ch_client", return_value=mock_client):
            # Also mock create_scheduler so we don't actually start one
            with patch("tushare_db.scheduler.service.create_scheduler"):
                with pytest.raises(SystemExit) as exc_info:
                    start_scheduler()

                assert exc_info.value.code == 2

    def test_start_scheduler_continues_if_trade_cal_populated(self):
        """If trade_cal has rows, start_scheduler should proceed."""
        from tushare_db.scheduler.service import start_scheduler

        mock_client = MagicMock()
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, idx: 1000
        mock_client.query.return_value.result_rows = [mock_row]

        mock_scheduler = MagicMock()
        mock_scheduler.get_jobs.return_value = []

        with patch("tushare_db.scheduler.jobs._get_ch_client", return_value=mock_client):
            with patch("tushare_db.scheduler.service.create_scheduler", return_value=mock_scheduler) as mock_create:
                with patch("tushare_db.scheduler.service.logger"):
                    start_scheduler()

                # Verify create_scheduler was called (pre-flight passed)
                mock_create.assert_called_once()


class TestIsTradingDayEmptyCal:
    """B8: _is_trading_day should raise if trade_cal is empty."""

    def test_empty_cal_raises_runtime_error(self):
        from tushare_db.scheduler.jobs import _is_trading_day

        mock_client = MagicMock()
        # is_open=1 query returns 0
        mock_client.query.return_value.result_rows = [(0,)]

        # But total count also returns 0
        def side_effect(sql):
            result = MagicMock()
            if "count()" in sql and "is_open" not in sql:
                result.result_rows = [(0,)]
            else:
                result.result_rows = [(0,)]
            return result

        mock_client.query.side_effect = side_effect

        with pytest.raises(RuntimeError, match="trade_cal not seeded"):
            _is_trading_day(mock_client, "20240102")
