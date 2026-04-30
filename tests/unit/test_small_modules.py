"""Tests for small uncovered modules: work_units, api_calls, sink, bootstrap.

Covers: UnitState, SyncRun, log_api_call, insert_rows, insert_with_version,
meta bootstrap DDL generation.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from unittest.mock import MagicMock, patch

import pytest


class TestUnitState:
    """planner/work_units.py — UnitState dataclass."""

    def test_default_values(self):
        from tushare_db.planner.work_units import UnitState
        state = UnitState()
        assert state.status == "pending"
        assert state.rows == 0
        assert state.attempts == 0
        assert state.last_error == ""

    def test_custom_values(self):
        from tushare_db.planner.work_units import UnitState
        state = UnitState(status="running", rows=100, attempts=2, last_error="timeout")
        assert state.status == "running"
        assert state.rows == 100

    def test_status_transitions(self):
        from tushare_db.planner.work_units import UnitState
        state = UnitState()
        state.status = "running"
        state.attempts += 1
        assert state.attempts == 1

        state.status = "done"
        state.rows = 500
        assert state.status == "done"
        assert state.rows == 500

    def test_biz_error_status(self):
        from tushare_db.planner.work_units import UnitState
        state = UnitState(status="biz_err", last_error="API not found")
        assert state.status == "biz_err"


class TestSyncRun:
    """planner/work_units.py — SyncRun dataclass."""

    def test_default_values(self):
        from tushare_db.planner.work_units import SyncRun
        run = SyncRun()
        assert run.status == "running"
        assert run.units_total == 0
        assert run.units_done == 0
        assert run.units_failed == 0

    def test_with_values(self):
        from tushare_db.planner.work_units import SyncRun
        run = SyncRun(
            run_id="abc-123",
            interface="stock_daily",
            batch="A",
            units_total=22,
            units_done=20,
            units_failed=2,
            status="partial",
        )
        assert run.run_id == "abc-123"
        assert run.status == "partial"
        assert run.units_done == 20


class TestLogApiCall:
    """meta/api_calls.py — log_api_call."""

    def test_logs_api_call(self):
        from tushare_db.meta.api_calls import log_api_call

        client = MagicMock()
        run_id = uuid.uuid4()

        log_api_call(client, run_id, "daily", 12345, 150, 200, 100)

        client.insert.assert_called_once()
        call_kwargs = client.insert.call_args[1]
        assert call_kwargs["table"] == "api_calls"
        assert call_kwargs["database"] == "_meta"

        data = call_kwargs["data"][0]
        assert data[1] == "daily"
        assert data[4] == 150  # duration_ms
        assert data[5] == 200  # status
        assert data[6] == 100  # rows

    def test_error_msg_truncated(self):
        from tushare_db.meta.api_calls import log_api_call

        client = MagicMock()
        run_id = uuid.uuid4()
        long_msg = "x" * 1000

        log_api_call(client, run_id, "income", 0, 5000, 500, 0, long_msg)

        data = client.insert.call_args[1]["data"][0]
        error_field = data[7]
        assert len(error_field) <= 500

    def test_default_empty_error(self):
        from tushare_db.meta.api_calls import log_api_call

        client = MagicMock()
        log_api_call(client, uuid.uuid4(), "daily", 0, 100, 200, 50)

        data = client.insert.call_args[1]["data"][0]
        assert data[7] == ""


class TestInsertRows:
    """sink/clickhouse_sink.py — insert_rows."""

    def test_empty_rows_returns_zero(self):
        from tushare_db.sink.clickhouse_sink import insert_rows

        client = MagicMock()
        result = insert_rows(client, "test_table", ["a", "b"], [])
        assert result == 0
        client.insert.assert_not_called()

    def test_inserts_rows_with_settings(self):
        from tushare_db.sink.clickhouse_sink import insert_rows

        client = MagicMock()
        rows = [["a", 1], ["b", 2]]
        result = insert_rows(client, "test_table", ["col1", "col2"], rows)

        assert result == 2
        client.insert.assert_called_once()
        call_kwargs = client.insert.call_args[1]
        assert call_kwargs["table"] == "test_table"
        assert call_kwargs["database"] == "tushare"
        assert call_kwargs["column_names"] == ["col1", "col2"]
        assert call_kwargs["data"] == rows
        assert "async_insert" in call_kwargs["settings"]

    def test_custom_database(self):
        from tushare_db.sink.clickhouse_sink import insert_rows

        client = MagicMock()
        result = insert_rows(client, "t", ["x"], [["1"]], database="_meta")
        assert result == 1
        assert client.insert.call_args[1]["database"] == "_meta"


class TestInsertWithVersion:
    """sink/clickhouse_sink.py — insert_with_version."""

    def test_appends_version_column(self):
        from tushare_db.sink.clickhouse_sink import insert_with_version

        client = MagicMock()
        with patch("tushare_db.sink.clickhouse_sink.insert_rows") as mock_insert:
            mock_insert.return_value = 2
            insert_with_version(client, "daily", ["ts_code", "close"], [["a", 1], ["b", 2]])

            mock_insert.assert_called_once()
            call_args = mock_insert.call_args
            # Positional args: (client, table, columns, rows, database)
            columns = call_args[0][2]
            data = call_args[0][3]
            assert "_version" in columns
            assert len(data) == 2
            assert len(data[0]) == 3  # ts_code, close, _version

    def test_version_already_in_columns(self):
        """If _version is already in columns, don't duplicate."""
        from tushare_db.sink.clickhouse_sink import insert_with_version

        client = MagicMock()
        with patch("tushare_db.sink.clickhouse_sink.insert_rows") as mock_insert:
            insert_with_version(
                client, "daily",
                ["ts_code", "_version"],
                [["a", 999]],
            )
            columns = mock_insert.call_args[0][2]
            assert columns.count("_version") == 1


class TestGetNativeClient:
    """sink/clickhouse_sink.py — get_native_client."""

    def test_defaults(self):
        from tushare_db.sink.clickhouse_sink import get_native_client

        with patch("tushare_db.sink.clickhouse_sink.clickhouse_connect.get_client") as mock_get:
            mock_get.return_value = MagicMock()
            get_native_client()

            mock_get.assert_called_once_with(
                host="localhost",
                port=8123,
                username="pipeline",
                password="",
                database="tushare",
                connect_timeout=10,
                send_receive_timeout=300,
            )

    def test_custom_params(self):
        from tushare_db.sink.clickhouse_sink import get_native_client

        with patch("tushare_db.sink.clickhouse_sink.clickhouse_connect.get_client") as mock_get:
            mock_get.return_value = MagicMock()
            get_native_client(host="myhost", port=9999, database="_meta")

            mock_get.assert_called_once_with(
                host="myhost",
                port=9999,
                username="pipeline",
                password="",
                database="_meta",
                connect_timeout=10,
                send_receive_timeout=300,
            )


class TestGetInterfaceStatus:
    """meta/sync_state.py — get_interface_status."""

    def test_returns_parsed_rows(self):
        from tushare_db.meta.sync_state import get_interface_status

        client = MagicMock()
        test_date = date(2024, 1, 1)
        client.query.return_value.result_rows = [
            ("daily:20240101", "done", 100, test_date, test_date, 1, ""),
            ("daily:20240102", "running", 0, None, test_date, 0, "timeout"),
        ]

        result = get_interface_status(client, "stock_daily")

        assert len(result) == 2
        assert result[0]["scope_key"] == "daily:20240101"
        assert result[0]["status"] == "done"
        assert result[0]["rows"] == 100
        assert result[0]["attempts"] == 1
        assert result[1]["last_error"] == "timeout"

    def test_escapes_interface_name(self):
        from tushare_db.meta.sync_state import get_interface_status

        client = MagicMock()
        client.query.return_value.result_rows = []
        get_interface_status(client, "stock' OR 1=1--")

        query = client.query.call_args[0][0]
        # escape_sql_str doubles single quotes: stock' → stock''
        assert "stock''" in query


class TestGetPendingUnits:
    """meta/sync_state.py — get_pending_units."""

    def test_returns_failed_and_partial(self):
        from tushare_db.meta.sync_state import get_pending_units

        client = MagicMock()
        client.query.return_value.result_rows = [
            ("daily:20240103", "failed", 3),
            ("daily:20240104", "partial", 1),
        ]

        result = get_pending_units(client, "stock_daily")

        assert len(result) == 2
        assert result[0]["scope_key"] == "daily:20240103"
        assert result[0]["status"] == "failed"
        assert result[0]["attempts"] == 3
        assert result[1]["status"] == "partial"

    def test_empty_result(self):
        from tushare_db.meta.sync_state import get_pending_units

        client = MagicMock()
        client.query.return_value.result_rows = []
        result = get_pending_units(client, "empty_interface")
        assert result == []
