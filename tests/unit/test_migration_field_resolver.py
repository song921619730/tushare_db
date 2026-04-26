"""Unit tests: migration field resolver."""

import pytest
from tushare_db.migration.field_resolver import (
    resolve_columns, should_normalize, normalize_value, diff_fields,
)


def test_resolve_columns_basic():
    pg_in, ch_in = resolve_columns(
        pg_cols=["ts_code", "trade_date", "open", "created_at", "updated_at"],
        ch_cols=["ts_code", "trade_date", "open", "_version"],
    )
    assert pg_in == ["ts_code", "trade_date", "open"]
    assert ch_in == ["ts_code", "trade_date", "open"]


def test_resolve_columns_with_rename():
    pg_in, ch_in = resolve_columns(
        pg_cols=["ts_code", "end_date", "unit_nav"],
        ch_cols=["ts_code", "cal_date", "unit_nav"],
        renames={"end_date": "cal_date"},
    )
    assert pg_in == ["ts_code", "end_date", "unit_nav"]
    assert ch_in == ["ts_code", "cal_date", "unit_nav"]


@pytest.mark.parametrize("col,expected", [
    ("total_revenue", True),
    ("total_mv", True),
    ("circ_mv", True),
    ("net_profit", True),
    ("vol", False),
    ("turnover_rate", False),
    ("pe_ttm", False),
    ("basic_eps", False),
    ("amount", True),
    ("buy_elg_amount", True),
    ("total_assets", True),
    ("total_liab", True),
    ("admin_expense", True),
    ("fin_expense", True),
    ("total_share", False),
])
def test_should_normalize(col, expected):
    assert should_normalize(col, "tushare_income") == expected


def test_normalize_value():
    assert normalize_value("total_revenue", 1000) == 10_000_000
    assert normalize_value("total_revenue", None) is None
    assert normalize_value("vol", 1000) == 1000


def test_share_only_normalizes_for_fund_tables():
    """*_share fields only normalize in fund_* tables."""
    assert should_normalize("total_share", "tushare_fund_portfolio") is True
    assert should_normalize("total_share", "tushare_stock_basic") is False


def test_diff_fields():
    diff = diff_fields(
        pg_cols=["ts_code", "trade_date", "close", "created_at", "updated_at"],
        ch_cols=["ts_code", "trade_date", "close", "_version"],
        renames={},
    )
    assert "ts_code" in diff["both"]
    assert "_version" in diff["ch_only_default"]
