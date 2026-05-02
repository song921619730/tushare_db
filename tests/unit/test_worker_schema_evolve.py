"""Tests for automatic schema evolution on missing columns."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch


class TestParseMissingColumns:
    """Test parse_missing_columns extracts column names from ClickHouse errors."""

    def test_unrecognized_column_single(self):
        from tushare_db.schema.evolver import parse_missing_columns
        msg = "DB::Exception: Code: 16. Unrecognized column 'name' (UNKNOWN_IDENTIFIER)"
        assert parse_missing_columns(msg) == ["name"]

    def test_unrecognized_column_without_quotes(self):
        from tushare_db.schema.evolver import parse_missing_columns
        msg = "DB::Exception: Code: 16. Unrecognized column name (UNKNOWN_IDENTIFIER)"
        assert parse_missing_columns(msg) == ["name"]

    def test_missing_columns_multi(self):
        from tushare_db.schema.evolver import parse_missing_columns
        msg = "Missing columns: 'lead_stock' 'industry' while processing query"
        assert parse_missing_columns(msg) == ["lead_stock", "industry"]

    def test_no_column_with_name(self):
        from tushare_db.schema.evolver import parse_missing_columns
        msg = "There is no column with name 'foo_bar'"
        assert parse_missing_columns(msg) == ["foo_bar"]

    def test_empty_string(self):
        from tushare_db.schema.evolver import parse_missing_columns
        assert parse_missing_columns("") == []

    def test_none_string(self):
        from tushare_db.schema.evolver import parse_missing_columns
        assert parse_missing_columns(None) == []

    def test_no_match(self):
        from tushare_db.schema.evolver import parse_missing_columns
        msg = "Connection refused"
        assert parse_missing_columns(msg) == []


class TestInsertWithEvolve:
    """Test _insert_with_evolve auto-evolves schema on missing column errors."""

    def _make_ch_client(self):
        client = MagicMock()
        return client

    def test_successful_insert_no_evolution(self):
        from tushare_db.runner.worker import _insert_with_evolve

        ch_client = self._make_ch_client()
        rows = [["000001.SZ", "平安银行", 100]]
        raw_items = [["000001.SZ", "平安银行", 100]]

        with patch("tushare_db.runner.worker.insert_with_version") as mock_insert:
            _insert_with_evolve(
                ch_client, table="tushare_test", columns=["ts_code", "name", "amount"],
                rows=rows, raw_items=raw_items,
            )
            mock_insert.assert_called_once()

    def test_missing_column_triggers_evolve_and_retry(self):
        from tushare_db.runner.worker import _insert_with_evolve

        ch_client = self._make_ch_client()
        ch_client.query.return_value.result_rows = [
            ("ts_code", "LowCardinality(String)"),
            ("name", "LowCardinality(String)"),
            ("amount", "Decimal64(4)"),
        ]
        raw_items = [["000001.SZ", "平安银行", 100]]
        rows = [["000001.SZ", "平安银行", 100]]

        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("DB::Exception: Code: 16. Unrecognized column 'extra_col'")

        with patch("tushare_db.runner.worker.insert_with_version", side_effect=side_effect) as mock_insert, \
             patch("tushare_db.runner.worker.evolve_schema") as mock_evolve, \
             patch("tushare_db.runner.worker.invalidate_column_cache") as mock_invalidate, \
             patch("tushare_db.runner.worker._normalize_items", return_value=rows) as mock_normalize:

            _insert_with_evolve(
                ch_client, table="tushare_test", columns=["ts_code", "name", "amount"],
                rows=rows, raw_items=raw_items,
            )

            mock_evolve.assert_called_once()
            assert "extra_col" in str(mock_evolve.call_args)
            mock_invalidate.assert_called_once()
            mock_normalize.assert_called_once()
            assert mock_insert.call_count == 2  # first failed, then retry

    def test_non_missing_column_error_propagates(self):
        from tushare_db.runner.worker import _insert_with_evolve

        ch_client = self._make_ch_client()
        rows = [["000001.SZ"]]
        raw_items = [["000001.SZ"]]

        with patch("tushare_db.runner.worker.insert_with_version", side_effect=Exception("Connection refused")):
            with pytest.raises(Exception, match="Connection refused"):
                _insert_with_evolve(
                    ch_client, table="tushare_test", columns=["ts_code"],
                    rows=rows, raw_items=raw_items,
                )
