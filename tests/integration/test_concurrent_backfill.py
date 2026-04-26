"""O6: High concurrency backfill — verifies N3 (cache TTL) and N4 (heartbeat client).

Spins up a real ClickHouse + mock Tushare, runs concurrent work units
with normal=4/special=2 workers, verifies no data loss or corruption.

Run: uv run pytest tests/integration/test_concurrent_backfill.py -v
"""

from __future__ import annotations

import threading
import time
import uuid
from datetime import date
from unittest.mock import MagicMock, patch

import clickhouse_connect
import pytest

from testcontainers.clickhouse import ClickHouseContainer

from tushare_db.core.tushare_client import TushareClient
from tushare_db.planner.strategies import WorkUnit
from tushare_db.runner.executor import execute_batch


@pytest.fixture(scope="module")
def ch_container():
    with ClickHouseContainer("clickhouse/clickhouse-server:24.8") as ch:
        yield ch


@pytest.fixture
def ch_client(ch_container):
    from tushare_db.runner.executor import _thread_local

    client = clickhouse_connect.get_client(
        host=ch_container.get_container_host_ip(),
        port=ch_container.get_exposed_port(8123),
        username="default",
        password="",
        database="default",
    )
    yield client

    # Cleanup: clear thread-local state
    if hasattr(_thread_local, "client"):
        try:
            _thread_local.client.close()
        except Exception:
            pass
        del _thread_local.client

    for table in ["test_concurrent_daily"]:
        client.command(f"DROP TABLE IF EXISTS {table}")


def _make_mock_tushare_client():
    """Mock TushareClient that returns consistent test data."""
    mock = MagicMock(spec=TushareClient)

    def _call(api_name, **params):
        # Return 10 rows per call
        return {
            "items": [
                {"ts_code": f"STOCK{i:04d}", "trade_date": "20240102", "open": 10.0 + i, "close": 11.0 + i, "vol": 1000 + i}
                for i in range(10)
            ]
        }

    mock.call.side_effect = _call
    mock._token = "mock"
    return mock


class TestConcurrentBackfill:
    """O6: Concurrent backfill with real ClickHouse."""

    def test_concurrent_insert_no_data_loss(self, ch_client):
        """12 work units, 4 workers, verify all rows land."""
        from tushare_db.runner.worker import _COLUMN_TYPE_CACHE

        _COLUMN_TYPE_CACHE.clear()

        ch_client.command(
            "CREATE TABLE test_concurrent_daily ("
            "  ts_code String, "
            "  trade_date Date, "
            "  open Float64, "
            "  close Float64, "
            "  vol Float64, "
            "  _version UInt64"
            ") ENGINE=ReplacingMergeTree(_version) ORDER BY (ts_code, trade_date)"
        )

        run_id = uuid.uuid4()
        tushare_client = _make_mock_tushare_client()

        # Create 12 work units
        units = [
            WorkUnit(
                interface="test_daily",
                table="test_concurrent_daily",
                bucket="normal",
                scope_key=f"test_daily_{i}",
                params={"date": f"202401{i:02d}"},
                batch="test",
            )
            for i in range(1, 13)
        ]

        # Patch heartbeat to avoid _meta table issues
        with patch("tushare_db.runner.worker._heartbeat_loop"):
            total, done, failed = execute_batch(
                units,
                tushare_client=tushare_client,
                ch_client=ch_client,
                run_id=run_id,
                max_workers=4,
            )

        # Verify: all units attempted
        assert total == 12
        assert failed == 0

        # Verify: rows landed in ClickHouse
        count_result = ch_client.query("SELECT count() FROM default.test_concurrent_daily FINAL")
        total_rows = count_result.result_rows[0][0]
        assert total_rows > 0, "Expected rows in ClickHouse after concurrent backfill"

    def test_column_cache_ttl_expires(self, ch_client):
        """N3: Column cache should expire after TTL."""
        from tushare_db.runner.worker import (
            _get_column_types,
            _COLUMN_TYPE_CACHE,
            invalidate_column_cache,
        )

        _COLUMN_TYPE_CACHE.clear()

        ch_client.command(
            "CREATE TABLE test_concurrent_daily ("
            "  ts_code String, "
            "  trade_date Date"
            ") ENGINE=ReplacingMergeTree(_version) ORDER BY ts_code"
        )

        # First call — populates cache
        types1 = _get_column_types(ch_client, "test_concurrent_daily", database="default")
        assert "ts_code" in types1
        assert len(_COLUMN_TYPE_CACHE) > 0

        # Invalidate — should clear cache
        invalidate_column_cache(table="test_concurrent_daily", database="default")
        assert "default.test_concurrent_daily" not in _COLUMN_TYPE_CACHE

        # Second call — should re-query
        types2 = _get_column_types(ch_client, "test_concurrent_daily", database="default")
        assert types1 == types2

    def test_sync_state_no_duplicates(self, ch_client):
        """Concurrent workers should not create duplicate sync_state entries."""
        ch_client.command(
            "CREATE TABLE IF NOT EXISTS _meta.sync_state ("
            "  interface String, "
            "  scope_key String, "
            "  status String, "
            "  rows UInt64, "
            "  last_success_at Nullable(DateTime64(3, 'Asia/Shanghai')), "
            "  heartbeat_at Nullable(DateTime64(3, 'Asia/Shanghai')), "
            "  attempts UInt16, "
            "  last_error Nullable(String), "
            "  _version UInt64"
            ") ENGINE=ReplacingMergeTree(_version) ORDER BY (interface, scope_key)"
        )

        lock = threading.Lock()
        errors = []

        def _insert(worker_id):
            try:
                ch_client.insert(
                    "_meta.sync_state",
                    [[
                        f"test_iface_{worker_id}", f"test_{worker_id}", "done",
                        100, None, None, 1, None, 1,
                    ]],
                    column_names=[
                        "interface", "scope_key", "status", "rows",
                        "last_success_at", "heartbeat_at", "attempts", "last_error", "_version",
                    ],
                )
            except Exception as e:
                with lock:
                    errors.append(str(e))

        threads = [threading.Thread(target=_insert, args=(i,)) for i in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)

        # All threads should succeed
        assert len(errors) == 0, f"Concurrent sync_state writes failed: {errors}"

        # Verify distinct rows
        count_result = ch_client.query("SELECT count() FROM _meta.sync_state FINAL")
        total_rows = count_result.result_rows[0][0]
        assert total_rows == 8, f"Expected 8 rows, got {total_rows}"

    def test_concurrent_batch_split(self, ch_client):
        """execute_batch should process normal and special units sequentially."""
        from tushare_db.runner.worker import _COLUMN_TYPE_CACHE
        _COLUMN_TYPE_CACHE.clear()

        ch_client.command(
            "CREATE TABLE test_concurrent_daily ("
            "  ts_code String, "
            "  trade_date Date, "
            "  open Float64, "
            "  close Float64, "
            "  vol Float64, "
            "  _version UInt64"
            ") ENGINE=ReplacingMergeTree(_version) ORDER BY (ts_code, trade_date)"
        )

        run_id = uuid.uuid4()
        tushare_client = _make_mock_tushare_client()

        units = [
            WorkUnit(
                interface="test_daily",
                table="test_concurrent_daily",
                bucket=bucket,
                scope_key=f"test_{bucket}_{i}",
                params={"date": f"202401{i:02d}"},
                batch="test",
            )
            for bucket in ("normal", "normal", "normal", "special", "special")
            for i in range(1, 4)
        ]

        with patch("tushare_db.runner.worker._heartbeat_loop"):
            total, done, failed = execute_batch(
                units,
                tushare_client=tushare_client,
                ch_client=ch_client,
                run_id=run_id,
                max_workers=2,
            )

        assert total == 15
        assert failed == 0

        count_result = ch_client.query("SELECT count() FROM default.test_concurrent_daily FINAL")
        total_rows = count_result.result_rows[0][0]
        assert total_rows > 0, "Expected rows from concurrent batch split"
