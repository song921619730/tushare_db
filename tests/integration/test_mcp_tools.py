"""Integration tests for MCP tools with real ClickHouse.

Covers: query_sql, describe_table, encoding — tools that need real data.
Note: describe_table enforces tushare/_meta database whitelist, so we test
query_sql with a real SELECT and describe_table with the whitelist.
"""

from __future__ import annotations

import json
import pytest
from datetime import date
from unittest.mock import patch

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
    for table in ["test_mcp_daily"]:
        client.command(f"DROP TABLE IF EXISTS {table}")


class TestQuerySqlIntegration:
    """query_sql with real ClickHouse — SELECT works, INSERT rejected."""

    def test_query_select_works(self, ch_client):
        from tushare_db.mcp_server.tools import query_sql

        with _patch_get_client(ch_client):
            result = query_sql("SELECT 1 AS x, 'hello' AS y")

        data = json.loads(result["content"])
        assert len(data) == 1
        assert data[0]["x"] == 1
        assert data[0]["y"] == "hello"

    def test_query_rejects_insert(self, ch_client):
        from tushare_db.mcp_server.tools import query_sql

        with _patch_get_client(ch_client):
            with pytest.raises(ValueError, match="Only SELECT"):
                query_sql("INSERT INTO tushare.test VALUES (1)")

    def test_query_rejects_drop(self, ch_client):
        from tushare_db.mcp_server.tools import query_sql

        with _patch_get_client(ch_client):
            with pytest.raises(ValueError, match="Only SELECT"):
                query_sql("DROP TABLE tushare.test")

    def test_query_returns_real_data(self, ch_client):
        from tushare_db.mcp_server.tools import query_sql

        ch_client.command(
            "CREATE TABLE test_mcp_daily (ts_code String, trade_date Date, close Float64) "
            "ENGINE=Memory"
        )
        ch_client.insert(
            "test_mcp_daily",
            [["000001.SZ", date(2024, 1, 2), 15.5]],
            column_names=["ts_code", "trade_date", "close"],
        )

        with _patch_get_client(ch_client):
            result = query_sql("SELECT ts_code, close FROM default.test_mcp_daily ORDER BY ts_code")

        data = json.loads(result["content"])
        assert len(data) == 1
        assert data[0]["ts_code"] == "000001.SZ"


def _patch_get_client(client):
    """Context manager that patches _get_client to return the given client."""
    def _fake_get_client():
        return client

    return patch("tushare_db.mcp_server.tools._get_client", _fake_get_client)


class TestDescribeTableIntegration:
    """describe_table with real ClickHouse — database whitelist + column info."""

    def test_rejects_system_database(self, ch_client):
        from tushare_db.mcp_server.tools import describe_table

        with _patch_get_client(ch_client):
            with pytest.raises(ValueError, match="Only tushare and _meta"):
                describe_table("system.users")

    def test_rejects_default_database(self, ch_client):
        from tushare_db.mcp_server.tools import describe_table

        with _patch_get_client(ch_client):
            with pytest.raises(ValueError, match="Only tushare and _meta"):
                describe_table("default.test_mcp_daily")

    def test_describe_with_tushare_prefix(self, ch_client):
        """describe_table with tushare.* prefix should attempt to query (may fail on missing table)."""
        from tushare_db.mcp_server.tools import describe_table

        with _patch_get_client(ch_client):
            # This will fail because the table doesn't exist, but the whitelist check passes
            try:
                result = describe_table("tushare.nonexistent_table")
                # If it somehow works, at least verify structure
                assert "columns" in result
            except Exception as e:
                # Expected: table doesn't exist
                assert "doesn't exist" in str(e) or "UNKNOWN_TABLE" in str(e)


class TestEncodeLargeResults:
    """B9: Arrow IPC + LZ4 encoding for large results."""

    def test_small_result_uses_json(self):
        from tushare_db.mcp_server.encoding import encode_response

        rows = [{"a": i} for i in range(10)]
        result = encode_response(rows)

        assert result["encoding"] == "json"
        assert result["row_count"] == 10

    def test_large_result_uses_arrow(self):
        from tushare_db.mcp_server.encoding import encode_response

        rows = [{"a": i, "b": f"row_{i}"} for i in range(1500)]
        result = encode_response(rows)

        assert result["encoding"] == "arrow_ipc_lz4"
        assert result["row_count"] == 1500
        assert "schema" in result

    def test_arrow_roundtrip(self):
        from tushare_db.mcp_server.encoding import encode_response, decode_response

        rows = [{"ts_code": "000001.SZ", "close": 15.5, "trade_date": "2024-01-02"}]
        rows.extend([{"ts_code": f"00000{i}.SZ", "close": float(i), "trade_date": f"2024-01-{i:02d}"} for i in range(3, 1503)])

        encoded = encode_response(rows)
        decoded = decode_response(encoded)

        assert len(decoded) == 1502
        assert decoded[0]["ts_code"] == "000001.SZ"

    def test_decode_json_response(self):
        """decode_response should handle JSON encoded responses too."""
        from tushare_db.mcp_server.encoding import encode_response, decode_response

        rows = [{"a": 1, "b": "test"}]
        encoded = encode_response(rows)
        decoded = decode_response(encoded)

        assert decoded == rows
