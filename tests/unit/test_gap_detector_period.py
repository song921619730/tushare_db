"""Tests for gap detector period gap detection."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch


class TestPeriodGapDetection:
    """Test _detect_period_gaps for financial tables."""

    def _make_mock_result(self, rows):
        """Create a mock query result."""
        m = MagicMock()
        m.result_rows = rows
        return m

    def test_detects_missing_quarters(self):
        """When Q2 is missing from a year with Q1/Q3/Q4, it should be detected."""
        from tushare_db.verify.gap_detector import _detect_period_gaps
        from tushare_db.config.models import InterfaceSpec, FetchStrategy

        spec = InterfaceSpec(
            name="income",
            table="tushare_income",
            enabled=True,
            priority="P0",
            mode="incremental",
            freq_bucket="normal",
            start_date="20230101",
            fetch_strategy=FetchStrategy(kind="period_loop", date_field="period"),
            partition_key="tuple()",
            order_by="ts_code, period",
            batch="normal",
        )

        mock_client = MagicMock()
        # Table exists
        mock_client.query.side_effect = [
            self._make_mock_result([(1,)]),  # table exists
            # Actual periods: 2023Q1, Q3, Q4 and 2024Q1, Q3 (missing 2023Q2, 2024Q2, 2024Q4)
            self._make_mock_result([
                ("20230331",), ("20230930",), ("20231231",),
                ("20240331",), ("20240930",),
            ]),
        ]

        results = _detect_period_gaps(mock_client, [spec])
        assert len(results) == 1
        assert results[0]["interface"] == "income"
        assert results[0]["gap_type"] == "financial_period"
        assert "20230630" in results[0]["missing_periods"]
        assert "20240630" in results[0]["missing_periods"]
        assert "20241231" in results[0]["missing_periods"]
        assert results[0]["missing_count"] == 3

    def test_empty_table_reported(self):
        """Empty financial table should be reported with issue flag."""
        from tushare_db.verify.gap_detector import _detect_period_gaps
        from tushare_db.config.models import InterfaceSpec, FetchStrategy

        spec = InterfaceSpec(
            name="balancesheet",
            table="tushare_balancesheet",
            enabled=True,
            priority="P0",
            mode="incremental",
            freq_bucket="normal",
            start_date="20240101",
            fetch_strategy=FetchStrategy(kind="period_loop", date_field="period"),
            partition_key="tuple()",
            order_by="ts_code, period",
            batch="normal",
        )

        mock_client = MagicMock()
        mock_client.query.side_effect = [
            self._make_mock_result([(1,)]),  # table exists
            self._make_mock_result([]),  # no data
        ]

        results = _detect_period_gaps(mock_client, [spec])
        assert len(results) == 1
        assert results[0]["issue"] == "Table has no data"
        assert results[0]["gap_type"] == "financial_period"

    def test_no_missing_quarters(self):
        """All quarters present should return no results."""
        from tushare_db.verify.gap_detector import _detect_period_gaps
        from tushare_db.config.models import InterfaceSpec, FetchStrategy

        spec = InterfaceSpec(
            name="cashflow",
            table="tushare_cashflow",
            enabled=True,
            priority="P0",
            mode="incremental",
            freq_bucket="normal",
            start_date="20230101",
            fetch_strategy=FetchStrategy(kind="period_loop", date_field="period"),
            partition_key="tuple()",
            order_by="ts_code, period",
            batch="normal",
        )

        mock_client = MagicMock()
        mock_client.query.side_effect = [
            self._make_mock_result([(1,)]),
            self._make_mock_result([
                ("20230331",), ("20230630",), ("20230930",), ("20231231",),
            ]),
        ]

        results = _detect_period_gaps(mock_client, [spec])
        assert len(results) == 0

    def test_table_not_exists_skipped(self):
        """Non-existent table should be skipped."""
        from tushare_db.verify.gap_detector import _detect_period_gaps
        from tushare_db.config.models import InterfaceSpec, FetchStrategy

        spec = InterfaceSpec(
            name="fina_indicator",
            table="tushare_fina_indicator",
            enabled=True,
            priority="P0",
            mode="incremental",
            freq_bucket="normal",
            start_date="20230101",
            fetch_strategy=FetchStrategy(kind="period_loop", date_field="period"),
            partition_key="tuple()",
            order_by="ts_code, period",
            batch="normal",
        )

        mock_client = MagicMock()
        mock_client.query.return_value = self._make_mock_result([(0,)])  # table doesn't exist

        results = _detect_period_gaps(mock_client, [spec])
        assert len(results) == 0

    def test_cross_year_period_range(self):
        """Periods spanning multiple years are correctly computed."""
        from tushare_db.verify.gap_detector import _detect_period_gaps
        from tushare_db.config.models import InterfaceSpec, FetchStrategy

        spec = InterfaceSpec(
            name="income",
            table="tushare_income",
            enabled=True,
            priority="P0",
            mode="incremental",
            freq_bucket="normal",
            start_date="20220101",
            fetch_strategy=FetchStrategy(kind="period_loop", date_field="period"),
            partition_key="tuple()",
            order_by="ts_code, period",
            batch="normal",
        )

        mock_client = MagicMock()
        mock_client.query.side_effect = [
            self._make_mock_result([(1,)]),
            # Only 2022Q4 and 2024Q1 present (missing all of 2023 and most of 2022/2024)
            self._make_mock_result([("20221231",), ("20240331",)]),
        ]

        results = _detect_period_gaps(mock_client, [spec])
        assert len(results) == 1
        missing = results[0]["missing_periods"]
        # 2022 Q1-Q3 should be missing
        assert "20220331" in missing
        assert "20220630" in missing
        assert "20220930" in missing
        # All 2023 quarters should be missing
        assert "20230331" in missing
        assert "20230630" in missing
        assert "20230930" in missing
        assert "20231231" in missing
        # 2024 Q2-Q4 should be missing
        assert "20240630" in missing
        assert "20240930" in missing
        assert "20241231" in missing
        # But 2022Q4 and 2024Q1 should NOT be missing (they're present)
        assert "20221231" not in missing
        assert "20240331" not in missing
