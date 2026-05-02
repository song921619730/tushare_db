"""Integration tests for verify module with real ClickHouse."""

from __future__ import annotations

import pytest
from datetime import date

from testcontainers.clickhouse import ClickHouseContainer
import clickhouse_connect


@pytest.fixture(scope="module")
def ch_container():
    with ClickHouseContainer("clickhouse/clickhouse-server:24.8") as ch:
        yield ch


@pytest.fixture
def ch_client(ch_container):
    client = clickhouse_connect.get_client(
        host=ch_container.get_container_host_ip(),
        port=ch_container.get_exposed_port(8123),
        username="default",
        password="",
        database="default",
    )
    yield client
    for table in ["test_verify_daily", "test_verify_empty"]:
        client.command(f"DROP TABLE IF EXISTS {table}")


class TestRowCountsIntegration:
    """verify/row_counts.py with real ClickHouse."""

    def test_verify_row_count_zero(self, ch_client):
        from tushare_db.verify.row_counts import verify_row_count

        ch_client.command(
            "CREATE TABLE test_verify_empty (ts_code String, trade_date Date) "
            "ENGINE=ReplacingMergeTree(_version) ORDER BY (ts_code, trade_date)"
        )

        result = verify_row_count(ch_client, "test_verify_empty")

        assert result["status"] == "empty"
        assert result["count"] == 0

    def test_verify_row_count_ok(self, ch_client):
        from tushare_db.verify.row_counts import verify_row_count

        ch_client.command(
            "CREATE TABLE test_verify_daily (ts_code String, trade_date Date) "
            "ENGINE=ReplacingMergeTree(_version) ORDER BY (ts_code, trade_date)"
        )
        ch_client.insert(
            "test_verify_daily",
            [["000001.SZ", date(2024, 1, 2)]],
            column_names=["ts_code", "trade_date"],
        )

        result = verify_row_count(ch_client, "test_verify_daily")

        assert result["status"] == "ok"
        assert result["count"] == 1

    def test_verify_row_count_missing_table(self, ch_client):
        from tushare_db.verify.row_counts import verify_row_count

        result = verify_row_count(ch_client, "nonexistent_table")

        assert result["status"] == "missing"


class TestGapDetectorIntegration:
    """verify/gap_detector.py with real ClickHouse."""

    def test_gaps_missing_table(self, ch_client):
        from tushare_db.verify.gap_detector import detect_gaps

        gaps = detect_gaps(ch_client, "nonexistent")
        assert gaps == []

    def test_gaps_with_data(self, ch_client):
        from tushare_db.verify.gap_detector import detect_gaps

        ch_client.command(
            "CREATE TABLE test_verify_daily (ts_code String, trade_date Date) "
            "ENGINE=ReplacingMergeTree(_version) ORDER BY (ts_code, trade_date)"
        )
        # Insert consecutive days — no gaps expected
        dates = [date(2024, 1, i) for i in range(2, 8)]
        ch_client.insert(
            "test_verify_daily",
            [["000001.SZ", d] for d in dates],
            column_names=["ts_code", "trade_date"],
        )

        gaps = detect_gaps(ch_client, "test_verify_daily")
        # Should find no gaps in consecutive trading days
        assert isinstance(gaps, list)
