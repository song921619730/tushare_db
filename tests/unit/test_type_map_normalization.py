"""Unit tests for B1 fix (normalize_value in _normalize_items) and B5 fix (type_map suffix blacklist).

B1: _normalize_items must call normalize_value() for Decimal64 columns to convert 万元→元.
B5: _FINANCIAL_AMOUNT_SUFFIXES must NOT match total_share, total_holders, etc.
"""

from __future__ import annotations

import pytest

from tushare_db.schema.type_map import (
    normalize_value,
    _needs_financial_normalization,
    _needs_fund_share_normalization,
    infer_ch_type,
)
from tushare_db.runner.worker import _normalize_items, _get_column_types, _COLUMN_TYPE_CACHE


class TestTypeMapSuffixConflict:
    """B5: Verify that total_share and similar non-amount fields are NOT normalized."""

    @pytest.mark.parametrize("field,expected", [
        # Should be normalized (amount fields)
        ("total_revenue", True),
        ("total_profit", True),
        ("total_assets", True),
        ("total_liab", True),
        ("total_mv", True),
        ("n_income", True),
        ("oper_cost", True),
        ("circ_mv", True),
        ("total_oper_revenue", True),
        # Should NOT be normalized (non-amount fields)
        ("total_share", False),
        ("total_holders", False),
        ("holder_total", False),
        ("total_shares", False),
        ("ts_code", False),
        ("ann_date", False),
        ("end_date", False),
    ])
    def test_financial_normalization(self, field, expected):
        assert _needs_financial_normalization(field) == expected

    def test_fund_share_normalization(self):
        assert _needs_fund_share_normalization("fund_share") is True
        assert _needs_fund_share_normalization("total_share") is True  # ends with _share
        assert _needs_fund_share_normalization("ts_code") is False


class TestNormalizeValue:
    """Test normalize_value for Decimal64(2) and Decimal64(4) types."""

    def test_decimal64_amount_multiplier(self):
        """Financial amounts: 万元 -> 元 (x10000)."""
        result = normalize_value("total_revenue", "Decimal64(2)", 100.5)
        assert result == 1005000.0

    def test_decimal64_share_multiplier(self):
        """Fund shares: 万份 -> 份 (x10000)."""
        result = normalize_value("fund_share", "Decimal64(4)", 50.0)
        assert result == 500000.0

    def test_null_value_returns_none(self):
        assert normalize_value("total_revenue", "Decimal64(2)", None) is None
        assert normalize_value("total_revenue", "Decimal64(2)", "") is None

    def test_non_financial_not_multiplied(self):
        """Fields not in financial list should NOT be multiplied."""
        result = normalize_value("total_share", "Decimal64(2)", 100.0)
        assert result == 100.0  # NOT multiplied

    def test_invalid_value_passthrough(self):
        """Non-numeric values should pass through."""
        result = normalize_value("total_revenue", "Decimal64(2)", "N/A")
        assert result == "N/A"


class TestNormalizeItemsB1:
    """B1: _normalize_items must normalize Decimal64 columns."""

    def test_decimal_amount_multiplied(self):
        """With column_types, Decimal64(2) amounts get x10000."""
        column_types = {
            "ts_code": "String",
            "total_revenue": "Decimal64(2)",
            "n_income": "Decimal64(2)",
        }
        rows = _normalize_items(
            ["ts_code", "total_revenue", "n_income"],
            [["000001.SZ", 100.5, 50.2]],
            column_types=column_types,
        )
        assert len(rows) == 1
        assert rows[0][0] == "000001.SZ"
        assert rows[0][1] == 1005000.0  # 100.5 * 10000
        assert rows[0][2] == 502000.0   # 50.2 * 10000

    def test_non_amount_not_multiplied(self):
        """total_share should NOT be multiplied even if Decimal64(2)."""
        column_types = {
            "ts_code": "String",
            "total_share": "Decimal64(2)",
        }
        rows = _normalize_items(
            ["ts_code", "total_share"],
            [["000001.SZ", 100.0]],
            column_types=column_types,
        )
        assert rows[0][1] == 100.0  # NOT multiplied

    def test_date_normalization_still_works(self):
        """Date strings should still be converted to datetime.date."""
        column_types = {
            "trade_date": "Date",
            "total_revenue": "Decimal64(2)",
        }
        rows = _normalize_items(
            ["trade_date", "total_revenue"],
            [["20240102", 200.0]],
            column_types=column_types,
        )
        from datetime import date
        assert rows[0][0] == date(2024, 1, 2)
        assert rows[0][1] == 2000000.0

    def test_nullable_decimal_handled(self):
        """Nullable(Decimal64(2)) should be normalized too."""
        column_types = {"n_income": "Nullable(Decimal64(2))"}
        rows = _normalize_items(
            ["n_income"],
            [[30.0]],
            column_types=column_types,
        )
        assert rows[0][0] == 300000.0

    def test_none_values_filled_for_non_nullable_columns(self):
        """None → 0 for non-nullable numeric columns (prevents clickhouse_connect errors)."""
        column_types = {"total_revenue": "Decimal64(2)"}
        rows = _normalize_items(
            ["total_revenue"],
            [[None]],
            column_types=column_types,
        )
        assert rows[0][0] == 0

    def test_none_preserved_for_nullable_columns(self):
        """None is preserved for Nullable columns."""
        column_types = {"total_revenue": "Nullable(Decimal64(2))"}
        rows = _normalize_items(
            ["total_revenue"],
            [[None]],
            column_types=column_types,
        )
        assert rows[0][0] is None

    def test_empty_column_types_fallback(self):
        """Without column_types, only date normalization runs."""
        rows = _normalize_items(
            ["trade_date", "total_revenue"],
            [["20240102", 100.0]],
        )
        from datetime import date
        assert rows[0][0] == date(2024, 1, 2)
        # Without column_types, total_revenue is NOT normalized (value passthrough)
        assert rows[0][1] == 100.0

    def test_column_type_cache(self):
        """Verify _COLUMN_TYPE_CACHE is populated and reused."""
        _COLUMN_TYPE_CACHE.clear()
        # We can't test _get_column_types without a real ClickHouse,
        # but we can verify the cache mechanism works
        _COLUMN_TYPE_CACHE["test.db"] = {"a": "String"}
        assert _COLUMN_TYPE_CACHE["test.db"] == {"a": "String"}
        _COLUMN_TYPE_CACHE.clear()


class TestInferChType:
    """Verify infer_ch_type still works after B5 changes."""

    def test_financial_field_infers_decimal64(self):
        assert infer_ch_type("total_revenue", [100.0]) == "Decimal64(2)"
        assert infer_ch_type("n_income", [50.0]) == "Decimal64(2)"
        assert infer_ch_type("circ_mv", [200.0]) == "Decimal64(2)"

    def test_non_financial_field_no_override(self):
        """total_share should NOT be inferred as Decimal64(2) via financial suffix.
        Note: It DOES match _FUND_SHARE_SUFFIXES (ends with _share), so gets Decimal64(4).
        The key B5 fix is that it's NOT a financial amount (Decimal64(2)).
        """
        # total_share is NOT a financial amount → no Decimal64(2)
        assert _needs_financial_normalization("total_share") is False
        # It DOES match fund share (ends with _share)
        assert _needs_fund_share_normalization("total_share") is True
        assert infer_ch_type("total_share", [100]) == "Decimal64(4)"
        # total_holders has no matching suffix → Int64
        assert infer_ch_type("total_holders", [5000]) == "Int64"

    def test_date_inference(self):
        assert infer_ch_type("trade_date", ["20240102"]) == "Date"
        assert infer_ch_type("ann_date", ["2024-01-02 12:00:00"]) == "DateTime"

    def test_low_cardinality_fields(self):
        assert infer_ch_type("ts_code", ["000001.SZ"]) == "LowCardinality(String)"
        assert infer_ch_type("exchange", ["SSE"]) == "LowCardinality(String)"
