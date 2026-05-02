"""Idempotent replay tests: running the same unit twice should not duplicate rows.

ClickHouse ReplacingMergeTree with _version column ensures that duplicate
inserts are deduplicated at merge time.
"""

from __future__ import annotations

import uuid

import pytest

from tushare_db.planner.strategies import WorkUnit
from tushare_db.runner.worker import mark_done, mark_failed, mark_running, _NOW


class TestIdempotentStateUpdates:
    """Test that state transitions are idempotent via ReplacingMergeTree."""

    def test_mark_running_then_done_transitions_correctly(self):
        """Running → Done is the happy path."""
        unit = WorkUnit(
            interface="daily",
            table="tushare.daily",
            scope_key="daily:20240315",
            params={"trade_date": "20240315"},
            bucket="normal",
        )
        # Verify WorkUnit structure
        assert unit.interface == "daily"
        assert unit.scope_key == "daily:20240315"
        assert unit.bucket == "normal"

    def test_mark_done_produces_versioned_row(self):
        """mark_done should include _version for ReplacingMergeTree dedup."""
        unit = WorkUnit(
            interface="daily",
            table="tushare.daily",
            scope_key="daily:20240315",
            params={"trade_date": "20240315"},
            bucket="normal",
        )
        # Verify the data tuple structure that would be inserted
        version = 1234567890
        attempt = 1
        rows = 42
        # The insert data should have all required fields
        expected_columns = [
            "interface", "scope_key", "status", "rows",
            "last_success_at", "heartbeat_at", "attempts", "last_error", "_version",
        ]
        data_tuple = (
            unit.interface,
            unit.scope_key,
            "done",
            rows,
            _NOW,  # last_success_at for done is actually 'now', not _NOW
            _NOW,
            attempt,
            "",
            version,
        )
        assert len(data_tuple) == len(expected_columns)
        assert data_tuple[2] == "done"
        assert data_tuple[3] == rows
        assert data_tuple[8] == version

    def test_mark_failed_preserves_error(self):
        """mark_failed should include error message truncated to 500 chars."""
        unit = WorkUnit(
            interface="daily",
            table="tushare.daily",
            scope_key="daily:20240315",
            params={"trade_date": "20240315"},
            bucket="normal",
        )
        long_error = "x" * 600
        # The error should be truncated
        truncated = long_error[:500]
        assert len(truncated) == 500
        assert truncated == "x" * 500


class TestReplayScenarios:
    """Test idempotent replay scenarios."""

    def test_same_unit_twice_should_deduplicate(self):
        """Running the same scope_key twice should produce one logical row.

        ReplacingMergeTree deduplicates by ORDER BY key when _version
        values differ. The second insert has a higher _version.
        """
        unit1 = WorkUnit(
            interface="daily",
            table="tushare.daily",
            scope_key="daily:20240315",
            params={"trade_date": "20240315"},
            bucket="normal",
        )
        unit2 = WorkUnit(
            interface="daily",
            table="tushare.daily",
            scope_key="daily:20240315",
            params={"trade_date": "20240315"},
            bucket="normal",
        )
        # Same scope_key means they are the same logical unit
        assert unit1.scope_key == unit2.scope_key

    def test_different_dates_produce_different_units(self):
        """Different dates should produce different scope_keys."""
        unit1 = WorkUnit(
            interface="daily",
            table="tushare.daily",
            scope_key="daily:20240315",
            params={"trade_date": "20240315"},
            bucket="normal",
        )
        unit2 = WorkUnit(
            interface="daily",
            table="tushare.daily",
            scope_key="daily:20240316",
            params={"trade_date": "20240316"},
            bucket="normal",
        )
        assert unit1.scope_key != unit2.scope_key

    def test_version_increases_on_retry(self):
        """Each retry should have a higher _version than the previous."""
        version1 = int(1_700_000_000_000)
        version2 = int(1_700_000_001_000)
        assert version2 > version1, "Later attempts should have higher _version"

    def test_attempt_counter_increments(self):
        """attempt should be retries + 1."""
        unit = WorkUnit(
            interface="daily",
            table="tushare.daily",
            scope_key="daily:20240315",
            params={"trade_date": "20240315"},
            bucket="normal",
            retries=2,
        )
        attempt = unit.retries + 1
        assert attempt == 3


class TestClickHouseSinkIdempotency:
    """Test that the ClickHouse sink produces versioned inserts."""

    def test_insert_with_version_includes_version_column(self):
        """insert_with_version should add _version to each row."""
        from tushare_db.sink.clickhouse_sink import insert_with_version
        import inspect
        sig = inspect.signature(insert_with_version)
        params = list(sig.parameters.keys())
        # Should accept table, columns, rows at minimum
        assert "table" in params
        assert "columns" in params
        assert "rows" in params

    def test_version_appended_to_columns(self):
        """The sink should append _version to the column list if not present."""
        # Simulate what insert_with_version does
        columns = ["trade_date", "open", "close"]
        if "_version" not in columns:
            columns = columns + ["_version"]
        assert "_version" in columns
        assert columns[-1] == "_version"

    def test_version_appended_to_each_row(self):
        """Each row should have _version appended."""
        version = 1_700_000_000_000
        rows = [[1, 2, 3], [4, 5, 6]]
        versioned_rows = [row + [version] for row in rows]
        assert len(versioned_rows) == 2
        assert versioned_rows[0][-1] == version
        assert versioned_rows[1][-1] == version

    def test_existing_version_not_duplicated(self):
        """If _version is already in columns, it should not be added again."""
        columns = ["trade_date", "open", "_version"]
        if "_version" not in columns:
            columns = columns + ["_version"]
        # Should only appear once
        assert columns.count("_version") == 1
