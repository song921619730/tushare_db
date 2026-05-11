"""Verify module unit tests: checksums, row_counts, gap_detector (mock only)."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

import pytest


class TestComputeChecksums:
    """verify/checksums.py — checksum computation."""

    def test_empty_latest_date_returns_empty(self):
        from tushare_db.verify.checksums import compute_checksums

        client = MagicMock()
        with patch("tushare_db.verify.checksums.load_interface_specs") as mock_specs, \
             patch("tushare_db.verify.checksums.get_latest_trade_date", return_value=None):
            mock_specs.return_value = [
                MagicMock(enabled=True, name="stock_daily", table="tushare_stock_daily", priority="P0"),
            ]
            result = compute_checksums(client)
            assert result == []

    def test_missing_table_skipped(self):
        from tushare_db.verify.checksums import compute_checksums

        client = MagicMock()
        client.query.return_value.result_rows = [(0,)]
        with patch("tushare_db.verify.checksums.load_interface_specs") as mock_specs, \
             patch("tushare_db.verify.checksums.get_latest_trade_date", return_value="20240101"):
            mock_specs.return_value = [
                MagicMock(enabled=True, name="missing_table", table="tushare_missing", priority="P0"),
            ]
            result = compute_checksums(client)
            assert result == []

    def test_checksum_computed_for_existing_table(self):
        from tushare_db.verify.checksums import compute_checksums

        client = MagicMock()
        mock_table = MagicMock()
        mock_table.result_rows = [(1,)]
        mock_fp = MagicMock()
        mock_fp.result_rows = [(100, 12345, 999)]
        client.query.side_effect = [mock_table, mock_fp]

        spec = MagicMock()
        spec.enabled = True
        spec.name = "stock_daily"
        spec.table = "tushare_stock_daily"
        spec.priority = "P0"

        with patch("tushare_db.verify.checksums.load_interface_specs", return_value=[spec]), \
             patch("tushare_db.verify.checksums.get_latest_trade_date", return_value="20240101"):
            result = compute_checksums(client, interface="stock_daily")

        assert len(result) == 1
        assert result[0]["interface"] == "stock_daily"
        assert result[0]["row_count"] == 100
        assert result[0]["fingerprint"] == "12345"
        assert result[0]["max_version"] == 999

    def test_checksum_filters_by_priority(self):
        from tushare_db.verify.checksums import compute_checksums

        p0 = MagicMock(enabled=True, name="daily", table="tushare_daily", priority="P0")
        p1 = MagicMock(enabled=True, name="weekly", table="tushare_weekly", priority="P1")

        with patch("tushare_db.verify.checksums.load_interface_specs", return_value=[p0, p1]), \
             patch("tushare_db.verify.checksums.get_latest_trade_date", return_value=None):
            result = compute_checksums(MagicMock(), priority="P0")

        assert result == []

    def test_checksum_error_caught(self):
        from tushare_db.verify.checksums import compute_checksums

        client = MagicMock()
        mock_table = MagicMock()
        mock_table.result_rows = [(1,)]
        client.query.side_effect = [mock_table, Exception("table too new")]

        spec = MagicMock()
        spec.enabled = True
        spec.name = "broken"
        spec.table = "tushare_broken"
        spec.priority = "P0"

        with patch("tushare_db.verify.checksums.load_interface_specs", return_value=[spec]), \
             patch("tushare_db.verify.checksums.get_latest_trade_date", return_value="20240101"):
            result = compute_checksums(client)

        assert len(result) == 1
        assert result[0]["error"] == "table too new"
        assert result[0]["row_count"] == 0
        assert result[0]["fingerprint"] is None


class TestVerifyRowCounts:
    """verify/row_counts.py — row count verification."""

    def test_missing_table_status(self):
        from tushare_db.verify.row_counts import verify_row_counts

        client = MagicMock()
        client.query.return_value.result_rows = [(0,)]

        spec = MagicMock()
        spec.enabled = True
        spec.name = "ghost"
        spec.table = "tushare_ghost"
        spec.priority = "P0"

        with patch("tushare_db.verify.row_counts.load_interface_specs", return_value=[spec]):
            result = verify_row_counts(client, interface="ghost")

        assert len(result) == 1
        assert result[0]["status"] == "missing"
        assert result[0]["issue"] == "Table does not exist"

    def test_empty_table_status(self):
        from tushare_db.verify.row_counts import verify_row_counts

        client = MagicMock()
        client.query.side_effect = [
            MagicMock(result_rows=[(1,)]),
            MagicMock(result_rows=[(0,)]),
            MagicMock(result_rows=[]),
        ]

        spec = MagicMock()
        spec.enabled = True
        spec.name = "empty_table"
        spec.table = "tushare_empty_table"
        spec.priority = "P0"

        with patch("tushare_db.verify.row_counts.load_interface_specs", return_value=[spec]):
            result = verify_row_counts(client, interface="empty_table")

        assert len(result) == 1
        assert result[0]["status"] == "empty"
        assert result[0]["row_count"] == 0

    def test_ok_status(self):
        from tushare_db.verify.row_counts import verify_row_counts

        client = MagicMock()
        client.query.side_effect = [
            MagicMock(result_rows=[(1,)]),
            MagicMock(result_rows=[(1000,)]),
            MagicMock(result_rows=[("done", 5)]),
        ]

        spec = MagicMock()
        spec.enabled = True
        spec.name = "good_table"
        spec.table = "tushare_good_table"
        spec.priority = "P0"

        with patch("tushare_db.verify.row_counts.load_interface_specs", return_value=[spec]):
            result = verify_row_counts(client, interface="good_table")

        assert len(result) == 1
        assert result[0]["status"] == "ok"
        assert result[0]["row_count"] == 1000
        assert result[0]["sync_done"] == 5

    def test_has_failures_status(self):
        from tushare_db.verify.row_counts import verify_row_counts

        client = MagicMock()
        client.query.side_effect = [
            MagicMock(result_rows=[(1,)]),
            MagicMock(result_rows=[(500,)]),
            MagicMock(result_rows=[("done", 3), ("failed", 2)]),
        ]

        spec = MagicMock()
        spec.enabled = True
        spec.name = "failing_table"
        spec.table = "tushare_failing_table"

        with patch("tushare_db.verify.row_counts.load_interface_specs", return_value=[spec]):
            result = verify_row_counts(client)

        assert result[0]["status"] == "has_failures"
        assert result[0]["sync_failed"] == 2

    def test_has_partial_status(self):
        from tushare_db.verify.row_counts import verify_row_counts

        client = MagicMock()
        client.query.side_effect = [
            MagicMock(result_rows=[(1,)]),
            MagicMock(result_rows=[(200,)]),
            MagicMock(result_rows=[("done", 2), ("partial", 1)]),
        ]

        spec = MagicMock()
        spec.enabled = True
        spec.name = "partial_table"
        spec.table = "tushare_partial_table"

        with patch("tushare_db.verify.row_counts.load_interface_specs", return_value=[spec]):
            result = verify_row_counts(client)

        assert result[0]["status"] == "has_partial"

    def test_table_name_prefix_added(self):
        from tushare_db.verify.row_counts import verify_row_counts

        client = MagicMock()
        client.query.return_value.result_rows = [(0,)]

        spec = MagicMock()
        spec.enabled = True
        spec.name = "no_prefix"
        spec.table = "tushare_no_prefix"

        with patch("tushare_db.verify.row_counts.load_interface_specs", return_value=[spec]):
            result = verify_row_counts(client)

        assert result[0]["table"] == "tushare.tushare_no_prefix"


class TestGapDetector:
    """verify/gap_detector.py — trading day gap detection."""

    def test_no_gaps_consecutive_days(self):
        from tushare_db.verify.gap_detector import _detect_date_gaps

        client = MagicMock()
        spec = MagicMock()
        spec.fetch_strategy.kind = "date_loop"
        spec.table = "tushare_daily"
        spec.name = "daily"

        cal_result = MagicMock()
        cal_result.result_rows = [(date(2024, 1, 1), date(2024, 1, 5))]

        table_check = MagicMock()
        table_check.result_rows = [(1,)]

        gap_result = MagicMock()
        gap_result.result_rows = []

        client.query.side_effect = [cal_result, table_check, gap_result]

        gaps = _detect_date_gaps(client, [spec], max_gap_days=1)
        assert gaps == []

    def test_gap_detected_missing_day(self):
        from tushare_db.verify.gap_detector import _detect_date_gaps

        client = MagicMock()
        spec = MagicMock()
        spec.fetch_strategy.kind = "date_loop"
        spec.table = "tushare_daily"
        spec.name = "daily"

        cal_result = MagicMock()
        cal_result.result_rows = [(date(2024, 1, 1), date(2024, 1, 3))]

        table_check = MagicMock()
        table_check.result_rows = [(1,)]

        gap_result = MagicMock()
        gap_result.result_rows = [(date(2024, 1, 2),)]

        client.query.side_effect = [cal_result, table_check, gap_result]

        gaps = _detect_date_gaps(client, [spec], max_gap_days=1)
        assert len(gaps) == 1
        assert gaps[0]["gap_type"] == "trading_day"

    def test_empty_synced_date_range_returns_empty(self):
        from tushare_db.verify.gap_detector import _detect_date_gaps

        client = MagicMock()
        cal_result = MagicMock()
        cal_result.result_rows = [(None, None)]

        client.query.return_value = cal_result

        spec = MagicMock()
        spec.fetch_strategy.kind = "date_loop"

        gaps = _detect_date_gaps(client, [spec], max_gap_days=1)
        assert gaps == []

    def test_financial_period_gap_detection(self):
        from tushare_db.verify.gap_detector import _detect_period_gaps

        client = MagicMock()
        spec = MagicMock()
        spec.fetch_strategy.kind = "period_loop"
        spec.fetch_strategy.date_field = None
        spec.table = "tushare_income"
        spec.name = "income"

        table_check = MagicMock()
        table_check.result_rows = [(1,)]

        period_result = MagicMock()
        period_result.result_rows = [("20231231",), ("20230930",)]

        client.query.side_effect = [table_check, period_result]

        gaps = _detect_period_gaps(client, [spec])
        assert len(gaps) == 1
        assert gaps[0]["gap_type"] == "financial_period"
        assert "20230630" in gaps[0]["missing_periods"]
        assert "20230331" in gaps[0]["missing_periods"]
