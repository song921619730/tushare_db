"""Integration tests: ClickHouse sink + normalize_value pipeline."""

from __future__ import annotations

import pytest

from testcontainers.clickhouse import ClickHouseContainer
import clickhouse_connect


@pytest.fixture(scope="module")
def ch_container():
    """Start a ClickHouse container for the module."""
    with ClickHouseContainer("clickhouse/clickhouse-server:24.8") as ch:
        yield ch


@pytest.fixture
def ch_client(ch_container):
    """Create a ClickHouse client for each test."""
    client = clickhouse_connect.get_client(
        host=ch_container.get_container_host_ip(),
        port=ch_container.get_exposed_port(8123),
        username="default",
        password="",
        database="default",
    )
    yield client
    # Cleanup: drop test tables
    for table in ["test_sink", "test_normalize_inc"]:
        client.command(f"DROP TABLE IF EXISTS {table}")


class TestClickHouseSink:
    """Integration: ClickHouse write path."""

    def test_insert_rows_basic(self, ch_client):
        """Basic insert should write all rows."""
        from tushare_db.sink.clickhouse_sink import insert_rows

        ch_client.command(
            "CREATE TABLE test_sink (a Int32, b String) ENGINE=Memory"
        )
        insert_rows(ch_client, "test_sink", ["a", "b"],
                     [[1, "x"], [2, "y"]], database="default")
        result = ch_client.query("SELECT count() FROM test_sink").result_rows
        assert result[0][0] == 2

    def test_insert_rows_empty(self, ch_client):
        """Empty insert should not fail."""
        from tushare_db.sink.clickhouse_sink import insert_rows

        ch_client.command(
            "CREATE TABLE test_sink (a Int32) ENGINE=Memory"
        )
        # Should not raise
        insert_rows(ch_client, "test_sink", ["a"], [], database="default")
        result = ch_client.query("SELECT count() FROM test_sink").result_rows
        assert result[0][0] == 0

    def test_insert_with_version(self, ch_client):
        """insert_with_version should append _version column."""
        from tushare_db.sink.clickhouse_sink import insert_with_version

        ch_client.command(
            "CREATE TABLE test_sink (a Int32, _version UInt64) "
            "ENGINE=ReplacingMergeTree(_version) ORDER BY a"
        )
        insert_with_version(
            ch_client,
            table="test_sink",
            columns=["a"],
            rows=[[1], [2]],
        )
        result = ch_client.query("SELECT a, _version FROM test_sink FINAL ORDER BY a").result_rows
        assert len(result) == 2
        assert result[0][1] > 0  # _version should be set


class TestNormalizeIntegration:
    """Integration: _normalize_items with real ClickHouse column types."""

    def test_decimal_amount_normalized(self, ch_client):
        """B1: Decimal64(2) financial columns should be ×10000."""
        from tushare_db.runner.worker import (
            _get_column_types, _normalize_items, _COLUMN_TYPE_CACHE,
        )
        _COLUMN_TYPE_CACHE.clear()

        ch_client.command(
            "CREATE TABLE test_normalize_inc ("
            "  ts_code String, "
            "  total_revenue Decimal64(2)"
            ") ENGINE=Memory"
        )

        types = _get_column_types(ch_client, "test_normalize_inc", database="default")
        assert "total_revenue" in types
        assert "Decimal64" in types["total_revenue"]

        rows = _normalize_items(
            ["ts_code", "total_revenue"],
            [["000001.SZ", 100.5]],
            column_types=types,
        )
        assert rows[0][0] == "000001.SZ"
        assert rows[0][1] == 1005000.0  # 万元 → 元

    def test_date_normalized(self, ch_client):
        """Date columns should be converted to datetime.date."""
        from tushare_db.runner.worker import _normalize_items
        from datetime import date

        rows = _normalize_items(
            ["trade_date"],
            [["20240102"]],
        )
        assert rows[0][0] == date(2024, 1, 2)

    def test_non_amount_not_multiplied(self, ch_client):
        """B5: total_share should NOT be multiplied."""
        from tushare_db.runner.worker import (
            _get_column_types, _normalize_items, _COLUMN_TYPE_CACHE,
        )
        _COLUMN_TYPE_CACHE.clear()

        ch_client.command(
            "CREATE TABLE test_normalize_inc ("
            "  ts_code String, "
            "  total_share Decimal64(2)"
            ") ENGINE=Memory"
        )

        types = _get_column_types(ch_client, "test_normalize_inc", database="default")
        rows = _normalize_items(
            ["ts_code", "total_share"],
            [["000001.SZ", 100.0]],
            column_types=types,
        )
        assert rows[0][1] == 100.0  # NOT multiplied
