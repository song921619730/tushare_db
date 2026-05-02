"""Scope key format validation for all six fetch strategies."""

from __future__ import annotations

import pytest

from tushare_db.planner.strategies import (
    build_scope_key,
    generate_full_once_units,
    generate_date_loop_units,
    generate_period_loop_units,
    generate_monthly_window_units,
    generate_per_symbol_period_units,
    generate_offset_paging_units,
)


class TestBuildScopeKey:
    """Test scope_key templates for each strategy."""

    def test_full_once_scope_key(self):
        """full_once: {interface}:full"""
        assert build_scope_key("stock_basic", "full_once") == "stock_basic:full"

    def test_date_loop_scope_key(self):
        """date_loop: {interface}:{trade_date:YYYYMMDD}"""
        assert build_scope_key("daily", "date_loop", trade_date="20240315") == "daily:20240315"

    def test_period_loop_scope_key(self):
        """period_loop: {interface}:{period:YYYYMMDD}"""
        assert build_scope_key("income", "period_loop", period="20240331") == "income:20240331"

    def test_monthly_window_scope_key(self):
        """monthly_window: {interface}:{ym:YYYYMM}"""
        assert build_scope_key("fund_nav", "monthly_window", ym="202403") == "fund_nav:202403"

    def test_per_symbol_period_scope_key(self):
        """per_symbol_period: {interface}:{ts_code}:{period:YYYYMMDD}"""
        assert build_scope_key("stk_factor", "per_symbol_period", ts_code="000001.SZ", period="20240331") == "stk_factor:000001.SZ:20240331"

    def test_offset_paging_scope_key(self):
        """offset_paging: {interface}:{date}:{offset:08d}"""
        assert build_scope_key("moneyflow", "offset_paging", date="20240315", offset="0") == "moneyflow:20240315:00000000"

    def test_offset_paging_nonzero_offset(self):
        """offset_paging with non-zero offset formats correctly."""
        assert build_scope_key("moneyflow", "offset_paging", date="20240315", offset="5000") == "moneyflow:20240315:00005000"

    def test_unknown_strategy_raises(self):
        """Unknown strategy raises ValueError."""
        with pytest.raises(ValueError, match="Unknown strategy"):
            build_scope_key("daily", "unknown")


class TestGenerateUnitsScopeKeys:
    """Test that generate_*_units produce correct scope_keys."""

    def test_full_once_generates_one_unit(self):
        units = generate_full_once_units("stock_basic", "normal", table="tushare.stock_basic")
        assert len(units) == 1
        assert units[0].scope_key == "stock_basic:full"
        assert units[0].interface == "stock_basic"
        assert units[0].params == {}

    def test_date_loop_generates_units_per_date(self):
        dates = ["20240313", "20240314", "20240315"]
        units = generate_date_loop_units("daily", "normal", dates, table="tushare.daily")
        assert len(units) == 3
        assert units[0].scope_key == "daily:20240313"
        assert units[1].scope_key == "daily:20240314"
        assert units[2].scope_key == "daily:20240315"
        assert units[0].params == {"trade_date": "20240313"}

    def test_period_loop_generates_units_per_quarter(self):
        units = generate_period_loop_units(
            "income", "normal", table="tushare.income",
            start_date="20240101", end_date="20241231",
        )
        # 4 quarters in 2024
        assert len(units) == 4
        assert units[0].scope_key == "income:20240331"
        assert units[1].scope_key == "income:20240630"
        assert units[2].scope_key == "income:20240930"
        assert units[3].scope_key == "income:20241231"

    def test_monthly_window_generates_units_per_month(self):
        units = generate_monthly_window_units(
            "fund_nav", "normal", table="tushare.fund_nav",
            start_date="20240101", end_date="20240331",
        )
        assert len(units) == 3
        assert units[0].scope_key == "fund_nav:202401"
        assert units[1].scope_key == "fund_nav:202402"
        assert units[2].scope_key == "fund_nav:202403"

    def test_per_symbol_period_generates_cartesian_product(self):
        symbols = ["000001.SZ", "000002.SZ"]
        units = generate_per_symbol_period_units(
            "stk_factor", "special", table="tushare.stk_factor",
            symbols=symbols,
            start_date="20240101", end_date="20240630",
        )
        # 2 symbols x 2 quarters (Q1, Q2)
        assert len(units) == 4
        scope_keys = {u.scope_key for u in units}
        assert "stk_factor:000001.SZ:20240331" in scope_keys
        assert "stk_factor:000001.SZ:20240630" in scope_keys
        assert "stk_factor:000002.SZ:20240331" in scope_keys
        assert "stk_factor:000002.SZ:20240630" in scope_keys

    def test_offset_paging_generates_units_per_date(self):
        dates = ["20240313", "20240314"]
        units = generate_offset_paging_units(
            "moneyflow", "normal", dates, page_size=5000, table="tushare.moneyflow",
        )
        assert len(units) == 2
        assert units[0].scope_key == "moneyflow:20240313:00000000"
        assert units[1].scope_key == "moneyflow:20240314:00000000"
        assert units[0].params["offset"] == 0
        assert units[0].params["limit"] == 5000

    def test_scope_keys_are_unique_per_strategy(self):
        """Different strategies produce different scope_keys for same interface."""
        date_key = build_scope_key("daily", "date_loop", trade_date="20240315")
        offset_key = build_scope_key("daily", "offset_paging", date="20240315", offset="0")
        assert date_key != offset_key
        assert date_key == "daily:20240315"
        assert offset_key == "daily:20240315:00000000"
