"""Planner and executor unit tests (mock only, no real connections).

Covers: _validate_date, get_trade_dates, get_symbols, plan_units strategies,
incremental get_latest_trade_date, get_target_date, filter_by_batch.
"""

from __future__ import annotations

import uuid
from datetime import date
from unittest.mock import MagicMock, patch

import pytest


class TestValidateDate:
    """planner.py — _validate_date."""

    def test_valid_date(self):
        from tushare_db.planner.planner import _validate_date
        assert _validate_date("20240101") == "20240101"

    def test_invalid_length(self):
        from tushare_db.planner.planner import _validate_date
        with pytest.raises(ValueError, match="Invalid date"):
            _validate_date("2024010")

    def test_non_digits(self):
        from tushare_db.planner.planner import _validate_date
        with pytest.raises(ValueError, match="Invalid date"):
            _validate_date("2024-01-01")

    def test_not_string(self):
        from tushare_db.planner.planner import _validate_date
        with pytest.raises(ValueError, match="Invalid date"):
            _validate_date(20240101)


class TestGetTradeDates:
    """planner.py — get_trade_dates."""

    def test_returns_formatted_dates(self):
        from tushare_db.planner.planner import get_trade_dates

        client = MagicMock()
        client.query.return_value.result_rows = [
            (date(2024, 1, 1),),
            (date(2024, 1, 2),),
        ]

        result = get_trade_dates(client, "20240101", "20240131")
        assert result == ["20240101", "20240102"]

    def test_validates_start_date(self):
        from tushare_db.planner.planner import get_trade_dates
        with pytest.raises(ValueError, match="Invalid date"):
            get_trade_dates(MagicMock(), "bad", "20240131")

    def test_validates_end_date(self):
        from tushare_db.planner.planner import get_trade_dates
        with pytest.raises(ValueError, match="Invalid date"):
            get_trade_dates(MagicMock(), "20240101", "bad")


class TestGetSymbols:
    """planner.py — get_symbols."""

    def test_returns_symbols(self):
        from tushare_db.planner.planner import get_symbols

        client = MagicMock()
        client.query.side_effect = [
            MagicMock(result_rows=[(1,)]),
            MagicMock(result_rows=[("000001.SZ",), ("600519.SH",)]),
        ]

        result = get_symbols(client)
        assert result == ["000001.SZ", "600519.SH"]

    def test_missing_stock_basic(self):
        from tushare_db.planner.planner import get_symbols

        client = MagicMock()
        client.query.return_value.result_rows = [(0,)]

        result = get_symbols(client)
        assert result == []


class TestPlanUnits:
    """planner.py — plan_units for all strategies."""

    def _make_spec(self, strategy: str, **kwargs):
        spec = MagicMock()
        spec.name = kwargs.get("name", "test_interface")
        spec.fetch_strategy = MagicMock()
        spec.fetch_strategy.kind = strategy
        spec.freq_bucket = kwargs.get("bucket", "normal")
        spec.table = kwargs.get("table", "tushare_test")
        spec.start_date = kwargs.get("start_date", "20200101")
        return spec

    def test_full_once_strategy(self):
        from tushare_db.planner.planner import plan_units

        spec = self._make_spec("full_once")
        with patch("tushare_db.planner.planner.generate_full_once_units") as mock_gen:
            mock_gen.return_value = [MagicMock()]
            result = plan_units(spec, MagicMock())
            assert len(result) == 1
            mock_gen.assert_called_once()

    def test_date_loop_strategy(self):
        from tushare_db.planner.planner import plan_units

        spec = self._make_spec("date_loop")
        client = MagicMock()
        client.query.return_value.result_rows = [(date(2024, 1, 1),)]

        with patch("tushare_db.planner.planner.generate_date_loop_units") as mock_gen:
            mock_gen.return_value = [MagicMock()]
            result = plan_units(spec, client)
            assert len(result) == 1
            mock_gen.assert_called_once()

    def test_period_loop_strategy(self):
        from tushare_db.planner.planner import plan_units

        spec = self._make_spec("period_loop")
        with patch("tushare_db.planner.planner.generate_period_loop_units") as mock_gen:
            mock_gen.return_value = [MagicMock()]
            result = plan_units(spec, MagicMock())
            assert len(result) == 1

    def test_monthly_window_strategy(self):
        from tushare_db.planner.planner import plan_units

        spec = self._make_spec("monthly_window")
        with patch("tushare_db.planner.planner.generate_monthly_window_units") as mock_gen:
            mock_gen.return_value = [MagicMock()]
            result = plan_units(spec, MagicMock())
            assert len(result) == 1

    def test_per_symbol_period_strategy(self):
        from tushare_db.planner.planner import plan_units

        spec = self._make_spec("per_symbol_period")
        client = MagicMock()
        client.query.side_effect = [
            MagicMock(result_rows=[(1,)]),
            MagicMock(result_rows=[("000001.SZ",)]),
        ]

        with patch("tushare_db.planner.planner.generate_per_symbol_period_units") as mock_gen:
            mock_gen.return_value = [MagicMock()]
            result = plan_units(spec, client)
            assert len(result) == 1

    def test_offset_paging_strategy(self):
        from tushare_db.planner.planner import plan_units

        spec = self._make_spec("offset_paging")
        client = MagicMock()
        client.query.return_value.result_rows = [(date(2024, 1, 1),)]

        with patch("tushare_db.planner.planner.generate_offset_paging_units") as mock_gen:
            mock_gen.return_value = [MagicMock()]
            result = plan_units(spec, client)
            assert len(result) == 1

    def test_unknown_strategy_raises(self):
        from tushare_db.planner.planner import plan_units

        spec = self._make_spec("unknown")
        with pytest.raises(ValueError, match="Unknown strategy"):
            plan_units(spec, MagicMock())

    def test_custom_date_range(self):
        from tushare_db.planner.planner import plan_units

        spec = self._make_spec("period_loop")
        with patch("tushare_db.planner.planner.generate_period_loop_units") as mock_gen:
            mock_gen.return_value = []
            plan_units(spec, MagicMock(), start_date="20230101", end_date="20231231")

            call_kwargs = mock_gen.call_args[1]
            assert call_kwargs["start_date"] == "20230101"
            assert call_kwargs["end_date"] == "20231231"


class TestIncremental:
    """runner/incremental.py — date and batch helpers."""

    def test_get_latest_trade_date(self):
        from tushare_db.runner.incremental import get_latest_trade_date

        client = MagicMock()
        client.query.return_value.result_rows = [(date(2024, 1, 5),)]
        result = get_latest_trade_date(client)
        assert result == "20240105"

    def test_get_latest_trade_date_empty(self):
        from tushare_db.runner.incremental import get_latest_trade_date

        client = MagicMock()
        client.query.return_value.result_rows = []
        result = get_latest_trade_date(client)
        assert result is None

    def test_get_target_date_returns_t_minus_1(self):
        from tushare_db.runner.incremental import get_target_date

        client = MagicMock()
        client.query.side_effect = [
            MagicMock(result_rows=[(date(2024, 1, 5),)]),
            MagicMock(result_rows=[(date(2024, 1, 4),)]),
        ]
        result = get_target_date(client)
        assert result == "20240104"

    def test_get_target_date_no_trading_day_before(self):
        from tushare_db.runner.incremental import get_target_date

        client = MagicMock()
        client.query.side_effect = [
            MagicMock(result_rows=[(date(2024, 1, 1),)]),
            MagicMock(result_rows=[]),
        ]
        result = get_target_date(client)
        assert result is None

    def test_filter_by_batch(self):
        from tushare_db.runner.incremental import filter_by_batch

        specs = [
            MagicMock(batch="A"),
            MagicMock(batch="B"),
            MagicMock(batch="A"),
        ]
        result = filter_by_batch(specs, "A")
        assert len(result) == 2
